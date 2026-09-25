# Copyright (C) 2009 Gabriel C. Stabel
# Copyright (C) 2009 Renato Lima (Akretion)
# Copyright (C) 2012 Raphaël Valyi (Akretion)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from collections import defaultdict

from erpbrasil.base.fiscal import cnpj_cpf

from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.osv import expression

from ..tools import check_cnpj_cpf, check_ie


class Partner(models.Model):
    _name = "res.partner"
    _inherit = [_name, "l10n_br_base.party.mixin"]

    @property
    def _rec_names_search(self):
        names = super()._rec_names_search
        # not "names +=": that would extend the parent class attribute in place
        return names + ["cnpj_cpf_stripped", "legal_name", "l10n_br_ie_code"]

    def _inverse_street_data(self):
        """In Brazil the address format is street_name, street_number
        (comma instead of space)"""
        br_partner_ids = self.filtered(lambda line: line._is_br_partner())
        not_br_partner = self - br_partner_ids
        for partner in br_partner_ids:
            street = (
                (partner.street_name or "") + ", " + (partner.street_number or "")
            ).strip()
            if partner.street_number2:
                street = street + " - " + partner.street_number2
            partner.street = street
        return super(Partner, not_br_partner)._inverse_street_data()

    l10n_br_rg_code = fields.Char(string="RG")

    pix_key_ids = fields.One2many(
        string="Pix Keys",
        comodel_name="res.partner.pix",
        inverse_name="partner_id",
        help="Keys for Brazilian instant payment (pix)",
    )

    is_br_partner = fields.Boolean(
        compute="_compute_br_partner",
        help="Is it a Brazilian partner?",
    )

    def copy_data(self, default=None):
        vals_list = super().copy_data(default=default)
        if not default or "vat" not in default:
            for partner, vals in zip(self, vals_list, strict=True):
                if partner.is_br_partner:
                    # CNPJ/CPF should be unique:
                    vals["vat"] = None
        return vals_list

    # In Brazil the CNPJ/CPF (vat) identifies a single taxpayer: unlike the
    # other commercial fields it is not shared between a company and its
    # contacts, who may have their own CPF. The core synchronization is kept
    # (only the changed fields, company dependent fields, batch import), with
    # two exceptions for the vat: the CNPJ/CPF of a Brazilian partner is not
    # copied (_update_fields_values), and a partner in Brazil does not get the
    # vat of its commercial partner (write, while syncing).

    def _commercial_sync_from_company(self):
        return super(
            Partner, self.with_context(l10n_br_commercial_sync=True)
        )._commercial_sync_from_company()

    def _commercial_sync_to_children(self, fields_to_sync=None):
        return super(
            Partner, self.with_context(l10n_br_commercial_sync=True)
        )._commercial_sync_to_children(fields_to_sync)

    def _load_records_create(self, vals_list):
        # an import syncs the commercial fields in batch, without the methods
        # above
        partners = super(
            Partner, self.with_context(l10n_br_commercial_sync=True)
        )._load_records_create(vals_list)
        return partners.with_env(self.env)

    def _update_fields_values(self, fields):
        """``self`` is the partner the values are copied from."""
        if "vat" in fields and self.is_br_partner:
            fields = [fname for fname in fields if fname != "vat"]
        return super()._update_fields_values(fields)

    def write(self, vals):
        if "vat" in vals and self.env.context.get("l10n_br_commercial_sync"):
            # The core writes the same values on every contact, but a partner
            # in Brazil keeps its own CPF/CNPJ: a foreign vat is not one, and
            # would fail its validation.
            if "country_id" in vals:
                in_brazil = vals["country_id"] == self.env.ref("base.br").id
                receivers = self if in_brazil else self.browse()
            else:
                receivers = self.filtered("is_br_partner")
            receivers = receivers.filtered(
                lambda partner: partner.commercial_partner_id != partner
                and partner.commercial_partner_id.vat == vals["vat"]
            )
            if receivers:
                if self - receivers:
                    super(Partner, self - receivers).write(vals)
                return super(Partner, receivers).write(
                    {fname: value for fname, value in vals.items() if fname != "vat"}
                )
        return super().write(vals)

    @api.constrains("vat", "l10n_br_ie_code")
    def _check_cnpj_l10n_br_ie_code(self):
        if self.env.context.get("disable_allow_cnpj_multi_ie") or self.env.context.get(
            "allow_vat_duplicate"
        ):
            return

        # Skip an empty normalized document (e.g. `vat = "/"`, which `base`
        # documents as "not subject to tax" and which normalizes to an empty
        # string): the domains below would otherwise match every other partner
        # with an empty document.
        records = self.filtered(lambda r: r.vat and r.cnpj_cpf_stripped)
        if not records:
            return

        # allow_cnpj_multi_ie is a res.config.settings boolean: it is stored
        # as "True" when enabled and removed entirely when disabled
        # (set_param deletes on a False bool), so a plain bool() reads it
        # correctly (absent -> strict), matching base_setup.show_effect.
        allow_cnpj_multi_ie = bool(
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("l10n_br_base.allow_cnpj_multi_ie")
        )

        # 18.0 stores `vat` unformatted (OCA/l10n-brazil#4671) and compares by
        # `vat` directly, so it is the key here; `cnpj_cpf_stripped` only
        # guards the empty document above.
        # One search for the records without parent; the others keep their
        # own search, whose domain also excludes the parent and its children.
        candidates_by_vat = defaultdict(list)
        vat_values = list(
            set(records.filtered(lambda r: not r.parent_id).mapped("vat"))
        )
        if vat_values:
            for candidate in self.env["res.partner"].search(
                [("vat", "in", vat_values)]
            ):
                candidates_by_vat[candidate.vat].append(candidate)

        for record in records:
            if record.parent_id:
                matches = record.env["res.partner"].search(
                    [
                        ("id", "not in", record.parent_id.ids),
                        ("parent_id", "not in", record.parent_id.ids),
                        ("vat", "=", record.vat),
                        ("id", "!=", record.id),
                        ("parent_id", "!=", record.id),
                    ]
                )
            else:
                # same filter as the domain above, in the search order
                matches = record.env["res.partner"].browse(
                    [
                        candidate.id
                        for candidate in candidates_by_vat[record.vat]
                        if candidate.id != record.id
                        and candidate.parent_id.id != record.id
                    ]
                )
            if matches:
                if cnpj_cpf.validar_cnpj(record.vat):
                    if allow_cnpj_multi_ie:
                        for partner in matches:
                            if (
                                partner.l10n_br_ie_code == record.l10n_br_ie_code
                                and record.l10n_br_ie_code
                            ):
                                raise ValidationError(
                                    self.env._(
                                        "There is already a partner %(name)s "
                                        "(ID %(partner_id)s) with this "
                                        "Estadual Inscription %(incr_est)s!",
                                        name=partner.name,
                                        partner_id=partner.id,
                                        incr_est=partner.l10n_br_ie_code,
                                    )
                                )
                    else:
                        raise ValidationError(
                            self.env._(
                                "There is already a partner %(name)s "
                                "(ID %(partner_id)s) with this CNPJ %(vat)s!",
                                name=matches[0].name,
                                partner_id=matches[0].id,
                                vat=record.vat,
                            )
                        )
                elif not record.is_company:
                    raise ValidationError(
                        self.env._(
                            "There is already a partner %(name)s (ID %(partner_id)s) "
                            "with this CPF/RG! %(vat)s",
                            name=matches[0].name,
                            partner_id=matches[0].id,
                            vat=matches[0].vat,
                        )
                    )

    @api.constrains("vat", "country_id")
    def _check_cnpj_cpf(self):
        for record in self:
            check_cnpj_cpf(
                record.env,
                record.vat,
                record.country_id,
            )

    @api.constrains("l10n_br_ie_code", "state_id", "is_company")
    def _check_ie(self):
        """Checks if company register number in field insc_est is valid,
        this method call others methods because this validation is State wise

        :Return: True or False.
        """
        for record in self:
            if record.is_company:
                check_ie(
                    record.env,
                    record.l10n_br_ie_code,
                    record.state_id,
                    record.country_id,
                )

    @api.constrains("state_tax_number_ids")
    def _check_state_tax_number_ids(self):
        """Checks if field other insc_est is valid,
        this method call others methods because this validation is State wise
        :Return: True or False.
        """
        codes_by_state = defaultdict(set)
        for line in self.state_tax_number_ids:
            codes_by_state[line.state_id.id].add(line.l10n_br_ie_code)
        partner_ids_by_key = defaultdict(list)
        if codes_by_state:
            domain = expression.OR(
                [
                    [
                        ("state_id", "=", state_id),
                        ("l10n_br_ie_code", "in", list(codes)),
                    ]
                    for state_id, codes in codes_by_state.items()
                ]
            )
            for partner in self.env["res.partner"].search(domain):
                key = (partner.state_id.id, partner.l10n_br_ie_code)
                partner_ids_by_key[key].append(partner.id)

        for record in self:
            for l10n_br_ie_code_line in record.state_tax_number_ids:
                check_ie(
                    record.env,
                    l10n_br_ie_code_line.l10n_br_ie_code,
                    l10n_br_ie_code_line.state_id,
                    record.country_id,
                )

                if l10n_br_ie_code_line.state_id.id == record.state_id.id:
                    raise ValidationError(
                        self.env._(
                            "There can only be one state tax"
                            " number per state for each partner!"
                        )
                    )
                key = (
                    l10n_br_ie_code_line.state_id.id,
                    l10n_br_ie_code_line.l10n_br_ie_code,
                )
                duplicate_ie = self.env["res.partner"].browse(
                    [pid for pid in partner_ids_by_key[key] if pid != record.id]
                )
                if duplicate_ie:
                    raise ValidationError(
                        self.env._(
                            "State Tax Number already used %(name)s",
                            name=duplicate_ie.name,
                        )
                    )

    @api.model
    def _address_fields(self):
        """Returns the list of address
        fields that are synced from the parent."""
        return super()._address_fields() + ["district"]

    @api.onchange("city_id")
    def _onchange_city_id(self):
        self.city = self.city_id.name

    def create_company(self):
        self.ensure_one()
        res = super(
            Partner, self.with_context(allow_vat_duplicate=True)
        ).create_company()
        if res and self.is_br_partner:
            parent = self.parent_id
            parent.legal_name = parent.name
            parent.l10n_br_ie_code = self.l10n_br_ie_code
            parent.l10n_br_im_code = self.l10n_br_im_code
        return res

    def _is_br_partner(self):
        """Check if is a Brazilian Partner."""
        if (
            self.country_id
            and self.country_id.code == "BR"
            or self.vat
            and (cnpj_cpf.validar_cnpj(self.vat) or cnpj_cpf.validar_cpf(self.vat))
        ):
            return True
        return False

    def _compute_br_partner(self):
        """Check if is a Brazilian Partner."""
        for record in self:
            record.is_br_partner = record._is_br_partner()

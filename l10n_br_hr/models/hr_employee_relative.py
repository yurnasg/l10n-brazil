# Copyright (C) 2026 - Present: Odoo Community Association (OCA)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from dateutil.relativedelta import relativedelta
from erpbrasil.base import misc
from odoo import api, fields, models
from odoo.addons.l10n_br_base.tools import check_cnpj_cpf
from odoo.exceptions import ValidationError

# eSocial Table 07: Dependent Types (Tabela 07 - Tipos de Dependente)
# Origin: eSocial Versão S-1.3 (NT 06/2026 rev.) / RFB IN 1.500/2014 & RIR/2018
# Note: Codes 04 and 07 were officially terminated on 25/04/2023 in eSocial
# and unified into 03 (Filho/Enteado) and 06 (Irmão/Neto).
# Maintained for historical data.
DEPENDENT_TYPES = [
    ("01", "01 - Spouse"),
    (
        "02",
        "02 - Cohabitant with common child or civil union",
    ),
    ("03", "03 - Child or stepchild"),
    (
        "04",
        "04 - Child or stepchild university/technical student",
    ),
    (
        "06",
        "06 - Sibling, grandchild, or great-grandchild under legal custody",
    ),
    (
        "07",
        (
            "07 - Sibling, grandchild, or great-grandchild university student "
            "under custody"
        ),
    ),
    ("09", "09 - Parents, grandparents, and great-grandparents"),
    ("10", "10 - Underprivileged minor under legal custody"),
    (
        "11",
        "11 - Incapacitated person (ward under guardianship/curatorship)",
    ),
    ("12", "12 - Former spouse"),
    ("99", "99 - Other Dependent"),
]

# Types ended on 25/04/2023: now the type below plus the student flag
ENDED_DEPENDENT_TYPES = {"04": "03", "07": "06"}


class HrEmployeeRelativeRelation(models.Model):
    """Mapping of HR Employee Relative Relation to legal dependent types."""

    _inherit = "hr.employee.relative.relation"

    dependent_type = fields.Selection(
        selection=[t for t in DEPENDENT_TYPES if t[0] not in ENDED_DEPENDENT_TYPES],
        string="Default Dependent Type",
        help="Default dependent classification for this relation.",
    )


class HrEmployeeRelative(models.Model):
    _inherit = "hr.employee.relative"

    vat = fields.Char(
        string="CPF",
        size=14,
        help="Taxpayer ID (CPF) of the dependent. Mandatory for tax dependency.",
    )

    dependent_type = fields.Selection(
        selection=DEPENDENT_TYPES,
        help="Dependent type classification for tax and social security purposes.",
    )

    is_irrf_dependent = fields.Boolean(
        string="IRRF Deduction",
        help=(
            "Indicates if the dependent qualifies for Income Tax (IRRF) "
            "monthly deduction."
        ),
    )

    is_family_allowance_dependent = fields.Boolean(
        string="Family Allowance",
        help=(
            "Indicates if the dependent qualifies for Family Allowance "
            "(Salário-Família)."
        ),
    )

    is_incapable = fields.Boolean(
        string="Incapable for Work",
        help=(
            "Indicates if the dependent is incapable of working / invalid "
            "(extends allowance and deduction beyond age limits)."
        ),
    )

    is_student = fields.Boolean(
        string="University / Technical Student",
        help=(
            "Child, stepchild, sibling, grandchild or great-grandchild attending "
            "university or technical school: IRRF deduction up to 24 years old. "
            "Replaces dependent types 04 and 07, ended on 25/04/2023."
        ),
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        res = super()._onchange_partner_id()
        if self.partner_id.vat:
            self.vat = misc.punctuation_rm(self.partner_id.vat)
        return res

    @api.onchange("relation_id")
    def _onchange_relation_id(self):
        if self.relation_id.dependent_type:
            self.dependent_type = self.relation_id.dependent_type
        self._onchange_dependent_rules()

    @api.onchange("date_of_birth", "dependent_type", "is_incapable", "is_student")
    def _onchange_dependent_rules(self):
        for record in self:
            has_age = False
            age = 0
            if record.date_of_birth:
                age = relativedelta(fields.Date.today(), record.date_of_birth).years
                has_age = True
            elif record.age_year:
                age = record.age_year
                has_age = True

            if record.is_incapable:
                record.is_family_allowance_dependent = True
                record.is_irrf_dependent = True
            elif record.dependent_type in ("03", "04", "06", "07", "10"):
                record.is_family_allowance_dependent = bool(has_age and age < 14)
                is_student = record.dependent_type in ENDED_DEPENDENT_TYPES or (
                    record.is_student and record.dependent_type in ("03", "06")
                )
                irrf_age_limit = 25 if is_student else 22
                record.is_irrf_dependent = bool(has_age and age < irrf_age_limit)
            elif record.dependent_type in ("01", "02"):
                record.is_irrf_dependent = True
                record.is_family_allowance_dependent = False

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("vat"):
                vals["vat"] = misc.punctuation_rm(vals["vat"])
        return super().create(vals_list)

    def write(self, vals):
        if vals.get("vat"):
            vals["vat"] = misc.punctuation_rm(vals["vat"])
        return super().write(vals)

    @api.constrains("vat", "is_irrf_dependent")
    def _check_irrf_dependent_vat(self):
        """eSocial requires the CPF of a dependent deducted from income tax."""
        for record in self:
            if record.is_irrf_dependent and not record.vat:
                raise ValidationError(
                    self.env._(
                        "The CPF of the dependent %(name)s is required for the "
                        "income tax (IRRF) deduction.",
                        name=record.name,
                    )
                )

    @api.constrains("dependent_type", "notes")
    def _check_other_dependent_description(self):
        """eSocial requires a description for the dependent type 99."""
        for record in self:
            if record.dependent_type == "99" and not (record.notes or "").strip():
                raise ValidationError(
                    self.env._(
                        "Describe in the notes the dependency of %(name)s "
                        "(dependent type 99 - Other).",
                        name=record.name,
                    )
                )

    @api.constrains("dependent_type")
    def _check_ended_dependent_type(self):
        """Ended types are kept on existing dependents, but can't be chosen."""
        for record in self:
            if record.dependent_type in ENDED_DEPENDENT_TYPES:
                raise ValidationError(
                    self.env._(
                        "Dependent types 04 and 07 ended on 25/04/2023: use type "
                        "%(dependent_type)s and mark the dependent as a university "
                        "or technical student.",
                        dependent_type=ENDED_DEPENDENT_TYPES[record.dependent_type],
                    )
                )

    @api.constrains("vat")
    def _check_vat(self):
        br_country = self.env.ref("base.br")
        for record in self:
            if not record.vat:
                continue
            if len(misc.punctuation_rm(record.vat)) != 11:
                raise ValidationError(
                    self.env._(
                        "The dependent's CPF must contain exactly 11 "
                        "digits (received: %(vat)s).",
                        vat=record.vat,
                    )
                )
            check_cnpj_cpf(record.env, record.vat, br_country)

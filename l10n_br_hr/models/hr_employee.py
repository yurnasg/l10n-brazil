# (c) 2014 Kmee - Rafael da Silva Lima <rafael.lima@kmee.com.br>
# (c) 2014 Kmee - Matheus Felix <matheus.felix@kmee.com.br>
# (c) 2016 KMEE Informática - Daniel Sadamo <daniel.sadamo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

import unicodedata

from erpbrasil.base import misc
from erpbrasil.base.fiscal import pis

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import street_split

from odoo.addons.l10n_br_base.tools import check_cnpj_cpf

from .hr_disability import OFFICIAL_ESOCIAL_CODES
from .hr_employee_relative import ENDED_DEPENDENT_TYPES

CERTIFICATE_BY_EDUCATION_LEVEL = {
    "09": "bachelor",
    "10": "graduate",
    "11": "master",
    "12": "doctor",
}


def _normalize_city_name(name):
    """Lowercase name without accents, to match a typed city name."""
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", (name or "").strip().lower())
        if not unicodedata.combining(char)
    )


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _default_country(self):
        company_country = self.env.company.country_id
        if not company_country or company_country.code == "BR":
            return self.env.ref("base.br", raise_if_not_found=False)
        return False

    country_of_birth = fields.Many2one(
        default=_default_country,
    )

    birth_city_id = fields.Many2one(comodel_name="res.city", groups="hr.group_hr_user")

    is_born_in_brazil = fields.Boolean(
        string="Born in Brazil",
        compute="_compute_is_born_in_brazil",
        store=True,
        groups="hr.group_hr_user",
        help="Indicates whether the employee was born in Brazil.",
    )

    @api.depends("country_of_birth", "birth_city_id", "country_id")
    def _compute_is_born_in_brazil(self):
        for record in self:
            if record.country_of_birth:
                record.is_born_in_brazil = record.country_of_birth.code == "BR"
            else:
                record.is_born_in_brazil = bool(
                    record.birth_city_id or record.country_id.code == "BR"
                )

    @api.onchange("birth_city_id")
    def _onchange_birth_city_id(self):
        if self.birth_city_id:
            self.place_of_birth = self.birth_city_id.name

    @api.onchange("country_of_birth")
    def _onchange_country_of_birth(self):
        if self.country_of_birth and self.country_of_birth.code != "BR":
            self.birth_city_id = False

    pis_pasep = fields.Char(
        string="PIS/PASEP",
        help=(
            "PIS/PASEP registration number. Optional field, as worker identification "
            "and government records have been unified under the CPF."
        ),
        groups="hr.group_hr_user",
    )

    pis_pasep_date = fields.Date(
        string="PIS/PASEP emission date", groups="hr.group_hr_user"
    )

    ctps = fields.Char(
        string="Physical CTPS number",
        help=(
            "Physical CTPS booklet number (optional, replaced by CPF "
            "for Digital CTPS under Portaria SEPRT 1.065/2019)."
        ),
        groups="hr.group_hr_user",
    )

    ctps_series = fields.Char(
        string="Physical CTPS series",
        help="Physical CTPS booklet series (optional).",
        groups="hr.group_hr_user",
    )

    ctps_date = fields.Date(
        string="Physical CTPS emission date",
        help="Physical CTPS emission date (optional).",
        groups="hr.group_hr_user",
    )

    ctps_uf_id = fields.Many2one(
        string="Physical CTPS state",
        comodel_name="res.country.state",
        domain=[("country_id.code", "=", "BR")],
        help="Physical CTPS state (optional).",
        groups="hr.group_hr_user",
    )

    creservist = fields.Char(
        string="Military certificate number",
        help="Military service certificate number (optional).",
        groups="hr.group_hr_user",
    )

    cresv_categ = fields.Selection(
        string="Military certificate category",
        selection=[
            ("1", "First Category"),
            ("2", "Second Category"),
            ("3", "Third Category"),
        ],
        help="Military service certificate category (optional).",
        groups="hr.group_hr_user",
    )

    identity_doc_type = fields.Many2one(
        related="work_contact_id.l10n_br_identity_doc_type",
        readonly=False,
        string="Identity Document Type",
        groups="hr.group_hr_user",
        help=(
            "Type of civil identity document. Under Law 14.534/2023 and Decree "
            "10.977/2022, CIN adopts the CPF as the sole and unique national "
            "ID number. Foreign workers typically use CRNM (formerly RNE)."
        ),
    )

    l10n_br_rg_code = fields.Char(
        related="work_contact_id.l10n_br_rg_code",
        readonly=False,
        help="National ID / RG / CIN number",
        groups="hr.group_hr_user",
    )

    l10n_br_identity_is_cpf_based = fields.Boolean(
        related="work_contact_id.l10n_br_identity_is_cpf_based",
        groups="hr.group_hr_user",
    )

    vat = fields.Char(
        string="CPF",
        related="work_contact_id.vat",
        readonly=False,
        groups="hr.group_hr_user",
        help="National Taxpayer ID (CPF) synchronized with the work contact partner.",
    )

    cpf = fields.Char(
        string="CPF (alias)",
        related="vat",
        readonly=False,
        groups="hr.group_hr_user",
        help="Compatibility alias pointing to vat.",
    )

    civil_name = fields.Char(
        string="Full Civil Name",
        related="work_contact_id.legal_name",
        readonly=False,
        groups="hr.group_hr_user",
        help=(
            "Civil name, as in the identity documents. The employee name is the "
            "name in use, which may be the social name."
        ),
    )

    organ_exp = fields.Char(string="Issuing agency", groups="hr.group_hr_user")

    rg_emission = fields.Date(
        string="National ID emission date", groups="hr.group_hr_user"
    )

    voter_title = fields.Char(
        string="Voter title",
        help="Voter registration title number (optional).",
        groups="hr.group_hr_user",
    )

    voter_zone = fields.Char(
        string="Voter zone",
        help="Voter registration electoral zone (optional).",
        groups="hr.group_hr_user",
    )

    voter_section = fields.Char(
        string="Voter section",
        help="Voter registration electoral section (optional).",
        groups="hr.group_hr_user",
    )

    driver_license = fields.Char(
        string="Driver license number", groups="hr.group_hr_user"
    )

    driver_categ = fields.Char(
        string="Driver license category", groups="hr.group_hr_user"
    )

    father_name = fields.Char(string="Father name", groups="hr.group_hr_user")

    mother_name = fields.Char(string="Mother name", groups="hr.group_hr_user")

    expiration_date = fields.Date(
        string="Driver license expiration date", groups="hr.group_hr_user"
    )

    ethnicity = fields.Many2one(
        string="Ethnicity / Race",
        comodel_name="hr.ethnicity",
        groups="hr.group_hr_user",
    )

    blood_type = fields.Selection(
        selection=[
            ("a+", "A+"),
            ("a-", "A-"),
            ("b+", "B+"),
            ("b-", "B-"),
            ("o+", "O+"),
            ("o-", "O-"),
            ("ab+", "AB+"),
            ("ab-", "AB-"),
        ],
        groups="hr.group_hr_user",
    )

    disability_ids = fields.Many2many(
        string="Disabilities",
        comodel_name="hr.disability",
        domain="['|', ('active', '=', True), ('id', 'in', disability_ids)]",
        context={"active_test": False},
        tracking=True,
        groups="hr.group_hr_user",
    )

    is_disability_quota = fields.Boolean(
        string="Fills Disability Quota",
        tracking=True,
        groups="hr.group_hr_user",
        help=(
            "Indicates if the employee fills the legal quota as a person "
            "with a disability (Law 8.213/1991, Art. 93)."
        ),
    )

    disability_notes = fields.Char(
        string="Disability Notes / Accessibility",
        size=255,
        groups="hr.group_hr_user",
        help=(
            "Specific details regarding accessibility, medical reports, "
            "or workplace adaptations (max 255 characters)."
        ),
    )

    has_legacy_disability = fields.Boolean(
        string="Disability Review Pending",
        compute="_compute_has_legacy_disability",
        store=True,
        index=True,
        groups="hr.group_hr_user",
    )

    legacy_seconded_review = fields.Boolean(
        string="Seconded Worker to Confirm",
        groups="hr.group_hr_user",
        help=(
            "Employee registered as seconded before the upgrade, which didn't tell "
            "whether the worker was received from or lent to another employer. "
            "Confirm the worker category (410 when received) and uncheck; setting "
            "the worker category also unchecks it."
        ),
    )

    needs_review = fields.Boolean(
        compute="_compute_needs_review",
        store=True,
        index=True,
        groups="hr.group_hr_user",
        help="The employee has data to review; the reasons are shown on the form.",
    )

    review_reasons = fields.Text(
        compute="_compute_review_reasons",
        groups="hr.group_hr_user",
    )

    identity_type_id = fields.Many2one(
        string="ID type", comodel_name="hr.identity.type", groups="hr.group_hr_user"
    )

    identity_validity = fields.Date(
        string="ID expiration date", groups="hr.group_hr_user"
    )

    identity_uf_id = fields.Many2one(
        string="ID expedition district",
        comodel_name="res.country.state",
        domain=[("country_id.code", "=", "BR")],
        groups="hr.group_hr_user",
    )

    identity_city_id = fields.Many2one(
        string="ID expedition city",
        comodel_name="res.city",
        domain="[('state_id','=',identity_uf_id)]",
        groups="hr.group_hr_user",
    )

    civil_certificate_type_id = fields.Many2one(
        string="Civil certificate type",
        comodel_name="hr.civil.certificate.type",
        groups="hr.group_hr_user",
    )

    professional_council_name = fields.Char(
        string="Council / Board",
        help="Professional council or board name (e.g. CREA, CRM, OAB, CRC, COREN).",
        groups="hr.group_hr_user",
    )

    professional_council_number = fields.Char(
        string="Council Registration Number",
        help="Professional council registration or license number.",
        groups="hr.group_hr_user",
    )

    professional_council_state_id = fields.Many2one(
        string="Council State",
        comodel_name="res.country.state",
        domain=[("country_id.code", "=", "BR")],
        help="State (UF) where the professional council registration was issued.",
        groups="hr.group_hr_user",
    )

    professional_council_validity = fields.Date(
        string="Council Expiration Date",
        help="Expiration date of the professional council license if applicable.",
        groups="hr.group_hr_user",
    )

    alternate_phone = fields.Char(groups="hr.group_hr_user")

    alternate_email = fields.Char(groups="hr.group_hr_user")

    private_address_is_br = fields.Boolean(
        compute="_compute_private_address_is_br",
        groups="hr.group_hr_user",
    )

    private_street_name = fields.Char(
        compute="_compute_private_street_data",
        inverse="_inverse_private_street_data",
        store=True,
        groups="hr.group_hr_user",
    )

    private_street_number = fields.Char(
        compute="_compute_private_street_data",
        inverse="_inverse_private_street_data",
        store=True,
        groups="hr.group_hr_user",
    )

    private_district = fields.Char(groups="hr.group_hr_user")

    private_city_id = fields.Many2one(
        string="Private Municipality",
        comodel_name="res.city",
        compute="_compute_private_city_id",
        store=True,
        readonly=False,
        domain="[('state_id', '=?', private_state_id)]",
        groups="hr.group_hr_user",
        help="Municipality with its IBGE code, kept in sync with the private city.",
    )

    registration = fields.Char(string="Registration number", groups="hr.group_hr_user")

    country_id = fields.Many2one(comodel_name="res.country", default=_default_country)

    is_foreign_worker = fields.Boolean(
        string="Foreign Worker",
        compute="_compute_is_foreign_worker",
        store=True,
        groups="hr.group_hr_user",
        help="Indicates if the employee has a nationality other than Brazil.",
    )

    is_naturalized = fields.Boolean(
        string="Naturalized Citizen",
        compute="_compute_is_naturalized",
        store=True,
        groups="hr.group_hr_user",
        help=(
            "Indicates if the employee is a naturalized Brazilian citizen "
            "(born abroad)."
        ),
    )

    naturalization_decree = fields.Char(
        string="Naturalization Ordinance / Decree",
        groups="hr.group_hr_user",
        help=(
            "Number of the Naturalization Ordinance / Decree published in the "
            "Official Gazette (DOU)."
        ),
    )

    naturalization_date = fields.Date(
        groups="hr.group_hr_user",
        help=(
            "Publication date of the Naturalization Ordinance in the "
            "Official Gazette (DOU)."
        ),
    )

    permit_no = fields.Char(
        help=(
            "Work authorization number. The immigration registration number (RNM) "
            "goes in the identity document number."
        ),
    )

    residence_term = fields.Selection(
        selection=[
            ("1", "Indefinite term"),
            ("2", "Fixed term"),
        ],
        groups="hr.group_hr_user",
        help=(
            "Term of residence in Brazil of the immigrant worker, as reported to "
            "eSocial (tmpResid)."
        ),
    )

    entry_condition = fields.Selection(
        selection=[
            ("1", "Refugee"),
            ("2", "Asylum seeker"),
            ("3", "Stay in Brazil for family reunion"),
            ("4", "Beneficiary of the Mercosur agreements"),
            (
                "5",
                (
                    "Dependent of a diplomatic or consular agent of a country with "
                    "a reciprocity agreement for paid work in Brazil"
                ),
            ),
            (
                "6",
                (
                    "Beneficiary of the Brazil-Portugal Treaty of Friendship, "
                    "Cooperation and Consultation"
                ),
            ),
            ("7", "Other condition"),
        ],
        groups="hr.group_hr_user",
        help=(
            "Condition under which the immigrant worker entered Brazil, as "
            "reported to eSocial (condIng)."
        ),
    )

    worker_category_id = fields.Many2one(
        comodel_name="hr.worker.category",
        tracking=True,
        groups="hr.group_hr_user",
        help=(
            "Worker employment category "
            "(e.g. CLT, Apprentice, Autonomous/Freelancer, Intern)."
        ),
    )

    contractor_partner_id = fields.Many2one(
        string="Contractor / Service Provider",
        comodel_name="res.partner",
        domain="[('is_company', '=', True)]",
        groups="hr.group_hr_user",
        help="Vendor / Outsourcing service provider employing this worker.",
    )

    education_level = fields.Selection(
        selection=[
            ("01", "01 - Illiterate"),
            ("02", "02 - Up to 5th grade incomplete (Primary Education)"),
            ("03", "03 - 5th grade complete (Primary Education)"),
            ("04", "04 - 6th to 9th grade incomplete (Lower Secondary Education)"),
            ("05", "05 - Lower Secondary Education Complete"),
            ("06", "06 - Upper Secondary Education Incomplete"),
            ("07", "07 - Upper Secondary Education Complete"),
            ("08", "08 - Incomplete Higher Education"),
            ("09", "09 - Complete Higher Education (Bachelor's/Licentiate)"),
            ("10", "10 - Postgraduate Complete (Specialization/MBA)"),
            ("11", "11 - Master's Degree Complete"),
            ("12", "12 - Doctorate Degree Complete"),
        ],
        groups="hr.group_hr_user",
        help="Worker formal education level.",
    )

    def _is_br_company(self):
        """Brazilian rules apply when the company is Brazilian or has no
        country."""
        self.ensure_one()
        country = self.company_id.country_id or self.env.company.country_id
        return not country or country.code == "BR"

    def _get_review_reasons(self):
        """Data a person must review on the employee; other modules add theirs."""
        self.ensure_one()
        reasons = []
        if self.has_legacy_disability:
            reasons.append(self.env._("The disability classification must be updated."))
        if self.legacy_seconded_review:
            reasons.append(self.env._("Seconded worker: confirm the worker category."))
        if self.job_id.cbo_id and not self.job_id.cbo_id.active:
            reasons.append(self.env._("The CBO of the job position is discontinued."))
        if any(
            dependent_type in ENDED_DEPENDENT_TYPES
            for dependent_type in self.relative_ids.mapped("dependent_type")
        ):
            reasons.append(
                self.env._("A dependent has a dependent type ended in 2023 (04 or 07).")
            )
        return reasons

    @api.depends(
        "has_legacy_disability",
        "legacy_seconded_review",
        "job_id.cbo_id.active",
        "relative_ids.dependent_type",
    )
    def _compute_needs_review(self):
        for employee in self:
            employee.needs_review = bool(employee._get_review_reasons())

    @api.depends(
        "has_legacy_disability",
        "legacy_seconded_review",
        "job_id.cbo_id.active",
        "relative_ids.dependent_type",
    )
    def _compute_review_reasons(self):
        for employee in self:
            employee.review_reasons = "\n".join(employee._get_review_reasons())

    @api.depends("private_country_id", "company_id.country_id")
    def _compute_private_address_is_br(self):
        for employee in self:
            if employee.private_country_id:
                employee.private_address_is_br = (
                    employee.private_country_id.code == "BR"
                )
            else:
                employee.private_address_is_br = employee._is_br_company()

    @api.depends("private_street")
    def _compute_private_street_data(self):
        for employee in self:
            street_data = street_split(employee.private_street)
            employee.private_street_name = street_data["street_name"] or False
            employee.private_street_number = street_data["street_number"] or False

    def _inverse_private_street_data(self):
        """Brazilian format "street name, number", keeping the complement typed
        after the number."""
        for employee in self:
            door_number = street_split(employee.private_street)["street_number2"]
            street = ", ".join(
                part
                for part in (
                    employee.private_street_name,
                    employee.private_street_number,
                )
                if part
            )
            if street and door_number:
                street = f"{street} - {door_number}"
            employee.private_street = street or False

    @api.depends("private_city", "private_state_id")
    def _compute_private_city_id(self):
        for employee in self:
            city = employee.private_city_id
            if not (
                city
                and city.state_id == employee.private_state_id
                and _normalize_city_name(city.name)
                == _normalize_city_name(employee.private_city)
            ):
                city = employee._find_private_city()
            employee.private_city_id = city

    def _find_private_city(self):
        """City of the private address state matching the typed city name,
        with or without accents."""
        self.ensure_one()
        city_name = _normalize_city_name(self.private_city)
        if not (city_name and self.private_state_id):
            return self.env["res.city"]
        cities = self.env["res.city"].search(
            [("state_id", "=", self.private_state_id.id)]
        )
        return cities.filtered(
            lambda city: _normalize_city_name(city.name) == city_name
        )[:1]

    @api.onchange("private_city_id")
    def _onchange_private_city_id(self):
        city = self.private_city_id
        if city:
            self.private_city = city.name
            self.private_state_id = city.state_id
            self.private_country_id = city.country_id or self.private_country_id

    @api.depends("country_id", "is_born_in_brazil")
    def _compute_is_naturalized(self):
        for record in self:
            record.is_naturalized = (
                record.country_id.code == "BR" and not record.is_born_in_brazil
            )

    @api.depends("country_id", "company_id.country_id")
    def _compute_is_foreign_worker(self):
        for record in self:
            record.is_foreign_worker = bool(
                record._is_br_company()
                and record.country_id
                and record.country_id.code != "BR"
            )

    def _get_default_identity_doc_type(self):
        """CIN for Brazilians and CRNM for foreigners, by nationality; no
        default outside a Brazilian company."""
        self.ensure_one()
        if not self._is_br_company():
            return False
        xmlid = (
            "l10n_br_base.identity_doc_type_crnm"
            if self.country_id and self.country_id.code != "BR"
            else "l10n_br_base.identity_doc_type_cin"
        )
        return self.env.ref(xmlid)

    @api.onchange("country_id")
    def _onchange_country_id_identity_doc_type(self):
        if not self.identity_doc_type or self.identity_doc_type.code in (
            "cin",
            "crnm",
        ):
            self.identity_doc_type = (
                self._get_default_identity_doc_type() or self.identity_doc_type
            )

    @api.onchange("education_level")
    def _onchange_education_level(self):
        if self.education_level:
            self.certificate = CERTIFICATE_BY_EDUCATION_LEVEL.get(
                self.education_level, "other"
            )

    @api.onchange("certificate")
    def _onchange_certificate(self):
        for level, certificate in CERTIFICATE_BY_EDUCATION_LEVEL.items():
            if self.certificate == certificate:
                self.education_level = level

    @api.onchange("worker_category_id")
    def _onchange_worker_category_id(self):
        if self.worker_category_id and self.worker_category_id.employee_type_default:
            self.employee_type = self.worker_category_id.employee_type_default

    @api.constrains("pis_pasep")
    def _validate_pis_pasep(self):
        for record in self:
            if record.pis_pasep and not pis.validar(record.pis_pasep):
                raise ValidationError(_("Invalid PIS/PASEP"))

    @api.constrains("vat", "country_id", "company_id")
    def _check_vat(self):
        br_country = self.env.ref("base.br")
        for record in self:
            if record.vat and (
                record._is_br_company() or record.country_id == br_country
            ):
                check_cnpj_cpf(record.env, record.vat, br_country)

    @api.onchange("vat", "identity_doc_type")
    def _onchange_l10n_br_identity_number(self):
        """Display only: in the form, related fields don't recompute the work
        contact, which computes the stored number on save."""
        cpf = "".join(char for char in self.vat or "" if char.isalnum())
        self.l10n_br_rg_code = self.env["res.partner"]._get_l10n_br_identity_number(
            self.identity_doc_type, cpf, self.l10n_br_rg_code
        )

    @api.model
    def _normalize_employee_vals(self, vals):
        """Store PIS/PASEP and CPF as digits only; a foreign tax ID is kept as
        typed."""
        if vals.get("pis_pasep"):
            vals["pis_pasep"] = misc.punctuation_rm(vals["pis_pasep"])
        for field_name in ("vat", "cpf"):
            digits = misc.punctuation_rm(vals.get(field_name) or "")
            if digits.isdigit() and len(digits) in (11, 14):
                vals[field_name] = digits
        # the private city record keeps the native private address in sync
        if vals.get("private_city_id"):
            city = self.env["res.city"].browse(vals["private_city_id"])
            vals.setdefault("private_city", city.name)
            vals.setdefault("private_state_id", city.state_id.id)
            if city.country_id:
                vals.setdefault("private_country_id", city.country_id.id)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._normalize_employee_vals(vals)
        employees = super().create(vals_list)
        # The work contact may only be created after super().create(), when
        # the related fields had no record to write on: write them on it.
        contact_fields = {
            "vat": "vat",
            "cpf": "vat",
            "l10n_br_rg_code": "l10n_br_rg_code",
            "identity_doc_type": "l10n_br_identity_doc_type",
            "civil_name": "legal_name",
        }
        for employee, vals in zip(employees, vals_list, strict=True):
            contact = employee.work_contact_id
            if not contact:
                continue
            contact_vals = {}
            for employee_field, contact_field in contact_fields.items():
                value = vals.get(employee_field)
                current = contact[contact_field]
                if contact._fields[contact_field].type == "many2one":
                    current = current.id
                if value and contact_field not in contact_vals and current != value:
                    contact_vals[contact_field] = value
            # a typed number without a type is kept as is, not replaced by
            # the CPF of a defaulted CIN
            if not (
                vals.get("identity_doc_type")
                or vals.get("l10n_br_rg_code")
                or contact.l10n_br_identity_doc_type
                or contact.l10n_br_rg_code
            ):
                default_doc_type = employee._get_default_identity_doc_type()
                if default_doc_type:
                    contact_vals["l10n_br_identity_doc_type"] = default_doc_type.id
            if contact_vals:
                contact.write(contact_vals)
        return employees

    def write(self, vals):
        self._normalize_employee_vals(vals)
        if vals.get("worker_category_id"):
            vals.setdefault("legacy_seconded_review", False)
        return super().write(vals)

    @api.model
    def _get_marital_status_selection(self):
        # "cohabitant" of hr already is the common-law marriage (união estável)
        return super()._get_marital_status_selection() + [
            ("separated", _("Separated")),
        ]

    @api.depends("disability_ids", "disability_ids.code", "disability_ids.active")
    def _compute_has_legacy_disability(self):
        for employee in self:
            employee.has_legacy_disability = any(
                not d.active or d.code not in OFFICIAL_ESOCIAL_CODES
                for d in employee.disability_ids
            )

    @api.constrains("is_disability_quota", "disability_ids")
    def _check_disability_quota(self):
        for employee in self:
            if employee.is_disability_quota and not employee.disability_ids:
                raise ValidationError(
                    _(
                        "To indicate that the employee fills the disability "
                        "quota, at least one disability must be selected."
                    )
                )

# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrContract(models.Model):
    _inherit = "hr.contract"
    _order = "employee_id"

    admission_type_id = fields.Many2one(
        string="Admission type", comodel_name="hr.contract.admission.type"
    )

    labor_bond_type_id = fields.Many2one(
        string="Labor bond type", comodel_name="hr.contract.labor.bond.type"
    )

    labor_regime_id = fields.Many2one(
        string="Labor regime",
        comodel_name="hr.contract.labor.regime",
        help="Labor legal regime (e.g. CLT, Statutory).",
    )

    has_legacy_labor_regime = fields.Boolean(
        compute="_compute_has_legacy_labor_regime",
        store=True,
        index=True,
        string="Labor Regime Review Flag",
        help="Indicates that the contract uses a discontinued labor regime.",
    )

    welfare_policy = fields.Selection(
        string="Welfare policy",
        selection=[
            ("rgps", "General Social Security Regime (RGPS)"),
            ("rpps", "Special Social Security Regime (RPPS)"),
            ("rpse", "Social Security Regime Abroad (RPSE)"),
        ],
        help="Social security policy regime (RGPS, RPPS, Abroad).",
    )

    salary_unit = fields.Many2one(comodel_name="hr.contract.salary.unit")

    weekly_hours = fields.Float(string="Weekly hours")

    monthly_hours = fields.Float(string="Monthly hours")

    work_schedule_type = fields.Selection(
        string="Work schedule regime",
        selection=[
            ("1", "1 - Subject to working hours"),
            ("2", "2 - External activity (CLT Art. 62, I)"),
            ("3", "3 - Specified position (CLT Art. 62, II)"),
            ("4", "4 - Telework (CLT Art. 62, III)"),
        ],
        help="Work schedule regime of the contract, as reported to eSocial (tpRegJor).",
    )

    partner_union = fields.Many2one(
        string="Union",
        comodel_name="res.partner",
        domain=[("union_entity_code", "!=", False)],
        help="Labor union partner with a defined union entity code "
        "(union_entity_code).",
    )

    union_name = fields.Char(
        string="Union Name", related="partner_union.name", readonly=True
    )

    union_cnpj = fields.Char(
        string="Union CNPJ", related="partner_union.vat", readonly=True
    )

    union_entity_code = fields.Char(
        string="Union entity code",
        related="partner_union.union_entity_code",
        readonly=True,
    )

    discount_union_contribution = fields.Boolean(
        string="Discount union contribution in admission"
    )

    resignation_date = fields.Date(string="Resignation date")

    resignation_cause_id = fields.Many2one(
        comodel_name="hr.contract.resignation.cause", string="Resignation cause"
    )

    notice_of_termination_id = fields.Many2one(
        string="Notice of termination type",
        comodel_name="hr.contract.notice.termination",
    )

    notice_of_termination_date = fields.Date(
        string="Notice of termination date",
    )

    legacy_termination_review = fields.Boolean(
        string="Termination Data to Review",
        help=(
            "Set by the upgrade when the published resignation cause or notice of "
            "termination has no equivalent in eSocial Table 19. Choose the current "
            "values and uncheck; changing them also unchecks it."
        ),
    )

    by_death = fields.Char(
        string="By death", help="Death certificate/Process/Beneficiary"
    )

    resignation_code = fields.Char(
        related="resignation_cause_id.code",
    )

    notice_of_termination_code = fields.Char(
        related="notice_of_termination_id.code",
    )

    @api.depends("labor_regime_id", "labor_regime_id.code", "labor_regime_id.active")
    def _compute_has_legacy_labor_regime(self):
        for contract in self:
            contract.has_legacy_labor_regime = bool(
                contract.labor_regime_id
                and (
                    not contract.labor_regime_id.active
                    or contract.labor_regime_id.code == "9"
                )
            )

    def _sync_employee_job(self):
        """Copy the job position of a draft or running contract to the employee."""
        for record in self:
            if (
                record.job_id
                and record.employee_id
                and record.state in ("draft", "open")
                and record.job_id != record.employee_id.job_id
            ):
                record.employee_id.job_id = record.job_id

    def set_job_in_employee(self):
        """Method kept for compatibility, delegating to _sync_employee_job."""
        return self._sync_employee_job()

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        res._sync_employee_job()
        for vals in vals_list:
            if vals.get("department_id") and vals.get("employee_id"):
                employee = self.env["hr.employee"].browse(vals.get("employee_id"))
                employee.department_id = vals.get("department_id")
        return res

    def write(self, vals):
        if "resignation_cause_id" in vals or "notice_of_termination_id" in vals:
            vals.setdefault("legacy_termination_review", False)
        res = super().write(vals)
        if "job_id" in vals or "employee_id" in vals:
            self._sync_employee_job()
        return res

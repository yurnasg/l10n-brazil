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
        help="e-Social: S2200/S2300 - tpRegTrab",
    )

    welfare_policy = fields.Selection(
        string="Welfare policy",
        selection=[
            ("rgps", "Regime Geral da Previdência Social"),
            ("rpps", "Regime Próprio da Previdência Social"),
            ("rpse", "Regime de Previdência Social no Exterior"),
        ],
        help="e-Social: S2200/S2300 - tpRegPrev",
    )

    salary_unit = fields.Many2one(
        string="Salary Unity", comodel_name="hr.contract.salary.unit"
    )

    weekly_hours = fields.Float(string="Weekly hours")

    monthly_hours = fields.Float(string="Monthly hours")

    partner_union = fields.Many2one(
        string="Sindicato",
        comodel_name="res.partner",
        domain=[("union_entity_code", "!=", False)],
        help="Sindicato é um partner que tem código de sindicato "
        "(union_entity_code) definido.",
    )

    union_name = fields.Char(
        string="Union", related="partner_union.name", readonly=True
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

    by_death = fields.Char(
        string="By death", help="Death certificate/Process/Beneficiary"
    )

    resignation_code = fields.Char(
        related="resignation_cause_id.code",
    )

    @api.onchange("employee_id")
    def _onchange_employee_id_set_default_job(self):
        for record in self:
            if record.employee_id and not record.job_id:
                record.job_id = record.employee_id.job_id

    def _sync_employee_job(self):
        for record in self:
            if (
                record.employee_id
                and record.job_id
                and record.state in ("draft", "open")
                and record.job_id != record.employee_id.job_id
            ):
                record.employee_id.with_context(alteracaocontratual=True).write(
                    {"job_id": record.job_id.id}
                )

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            if record.department_id and record.employee_id:
                record.employee_id.department_id = record.department_id
        res._sync_employee_job()
        return res

    def write(self, vals):
        res = super().write(vals)
        if "job_id" in vals or "state" in vals:
            self._sync_employee_job()
        return res

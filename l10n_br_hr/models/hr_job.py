# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrJob(models.Model):
    _inherit = "hr.job"

    cbo_id = fields.Many2one(
        string="CBO",
        comodel_name="l10n_br_hr.cbo",
        domain=[("internal_type", "=", "normal"), ("active", "=", True)],
    )

    cbo_is_archived = fields.Boolean(
        compute="_compute_cbo_is_archived",
        string="CBO Archived Flag",
    )

    @api.depends("cbo_id", "cbo_id.active")
    def _compute_cbo_is_archived(self):
        for job in self:
            job.cbo_is_archived = bool(job.cbo_id and not job.cbo_id.active)

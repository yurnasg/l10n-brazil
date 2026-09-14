# Copyright (C) 2026 - Present KMEE, Odoo Community Association (OCA)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _get_review_reasons(self):
        reasons = super()._get_review_reasons()
        if any(self.contract_ids.mapped("has_legacy_labor_regime")):
            reasons.append(self.env._("A contract uses a discontinued labor regime."))
        if any(self.contract_ids.mapped("legacy_termination_review")):
            reasons.append(self.env._("A contract has termination data to review."))
        return reasons

    @api.depends(
        "contract_ids.has_legacy_labor_regime",
        "contract_ids.legacy_termination_review",
    )
    def _compute_needs_review(self):
        return super()._compute_needs_review()

    @api.depends(
        "contract_ids.has_legacy_labor_regime",
        "contract_ids.legacy_termination_review",
    )
    def _compute_review_reasons(self):
        return super()._compute_review_reasons()

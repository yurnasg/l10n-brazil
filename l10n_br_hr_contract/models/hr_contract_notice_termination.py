# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractNoticeTermination(models.Model):
    """Notice of Termination Type (1: Worked, 2: Indemnified, 3: Not applicable).

    Origin / Legal Basis:
    - Legal Basis: CLT Art. 487 and Law 12.506/2011 (proportional notice).
    - eSocial event S-2299 (layout S-1.3) has no notice type field: it reports
      the notice date (dtAvPrv) and whether the notice was indemnified
      (indPagtoAPI = S), which is code 2.
    """

    _name = "hr.contract.notice.termination"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Notice of Termination Type"

    name = fields.Char(string="Notice of termination type", translate=True)

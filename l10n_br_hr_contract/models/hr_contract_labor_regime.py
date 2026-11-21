# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class HrContractLaborRegime(models.Model):
    """Labor Regime (eSocial Event S-2200 - tpRegTrab).

    Origin / Legal Basis:
    - Official Source: eSocial - Governo Federal / MTE
    - Event: S-2200 (Cadastramento Inicial e Admissão)
    - Field: tpRegTrab (1: CLT, 2: Estatutário / legislações específicas)
    - Layout Version: eSocial Versão S-1.3 (NT 06/2026 rev.)
    - Legal Basis: CLT (Decreto-Lei nº 5.452/1943) e Legislação Previdenciária.
    - Archival Policy: RJU and RJP (code 9 of the previous table) are kept
      archived; contracts using them are flagged for review.
    """

    _name = "hr.contract.labor.regime"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Labor Regime"
    _rec_names_search = ("code", "short_name", "name")

    name = fields.Char(string="Labor regime", translate=True)

    short_name = fields.Char()

    code = fields.Char(size=1)

    @api.depends("name", "short_name")
    def _compute_display_name(self):
        for record in self:
            if record.short_name:
                record.display_name = f"{record.short_name} - {record.name}"
            else:
                record.display_name = record.name

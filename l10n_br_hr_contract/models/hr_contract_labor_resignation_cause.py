# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractResignationCause(models.Model):
    """eSocial Table 19: Resignation Causes & FGTS Withdrawal Codes.

    Origin / Legal Basis:
    - Official Source: eSocial - Governo Federal / Caixa Econômica Federal / MTE
    - Table: Tabela 19 - Motivos de Desligamento / Evento S-2299
    - Layout Version: eSocial Versão S-1.3 (NT 06/2026 rev., 09/04/2026)
    - Legal Basis: CLT (Decreto-Lei nº 5.452/1943), Lei nº 8.036/1990 (FGTS)
      e Circular CAIXA nº 998/2022 (Manual de Movimentação do FGTS)
    - Archival Policy: codes with an end date in Table 19 are kept archived
      (active=False): 14 (21/01/2024) and 31 (17/09/2024). Codes that ended
      before (15, 18-20, 28, 35) are not loaded. The causes of the previous
      version (RAIS codes) are mapped by meaning in the 18.0.1.3.0 migration.
    """

    _name = "hr.contract.resignation.cause"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Resignation Causes"

    name = fields.Char(string="Resignation cause", translate=True)

    code = fields.Char(string="Resignation cause code")

    fgts_withdraw_code = fields.Char(string="FGTS withdrawal code")

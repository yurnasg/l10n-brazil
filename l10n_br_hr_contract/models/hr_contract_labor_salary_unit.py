# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractSalaryUnit(models.Model):
    """Salary Unit of Payment (eSocial Event S-2200 - undSalFixo).

    Origin / Legal Basis:
    - Official Source: eSocial - Governo Federal / MTE
    - Event: S-2200 (Cadastramento Inicial e Admissão)
    - Field: undSalFixo (1: Por hora, 2: Por dia, 3: Por semana, 4: Por quinzena,
      5: Por mês, 6: Por tarefa, 7: Não aplicável - exclusivamente variável)
    - Layout Version: eSocial Versão S-1.3 (NT 06/2026 rev.)
    - Legal Basis: CLT Art. 458 e seguintes.
    """

    _name = "hr.contract.salary.unit"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Salary Unit"

    name = fields.Char(string="Salary Unit", translate=True)

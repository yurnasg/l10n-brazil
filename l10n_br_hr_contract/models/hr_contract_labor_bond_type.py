# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractLaborBondType(models.Model):
    """Labor Bond Type according to RAIS/CAGED nomenclature.

    Origin / Legal Basis:
    - Official Source: Ministério do Trabalho e Previdência (MTP / MTE)
    - Table: Tabela de Vínculos Empregatícios da RAIS / CAGED (Códigos 10 a 97)
    - Reference: Manual de Orientação da RAIS (Ano-Base 2023/2024)
    - Legal Basis: Portaria MTP / Decreto Federal nº 76.900/1975.
    - Note: Legacy pre-eSocial table maintained for historical employee contracts.
    """

    _name = "hr.contract.labor.bond.type"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Labor Bond Type (RAIS / CAGED)"

    name = fields.Char(string="Labor bond type", translate=True)

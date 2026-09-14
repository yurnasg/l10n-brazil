# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# Copyright 2025 Akretion - Renato Lima <renato.lima@akretion.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrContractAdmissionType(models.Model):
    """Employee Admission Type (eSocial Event S-2200 - tpAdmissao).

    Origin / Legal Basis:
    - Official Source: eSocial - Governo Federal / MTE
    - Event: S-2200 (Cadastramento Inicial e Admissão)
    - Field: tpAdmissao (1: Admissão, 2: Transf. mesmo grupo, 3: Transf. consórcio,
      4: Sucessão/incorporação/cisão/fusão, 5: Transf. do empregado doméstico,
      6: Mudança de CPF, 7: Transf. quando a empresa sucedida é inapta)
    - Layout Version: eSocial Versão S-1.3 (NT 06/2026 rev.)
    - Legal Basis: Manual de Orientação do eSocial (MOS) e CLT.
    """

    _name = "hr.contract.admission.type"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Admission Type"

    name = fields.Char(string="Admission type", translate=True)

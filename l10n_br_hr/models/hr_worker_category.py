# Copyright (C) 2026 - Present KMEE, Odoo Community Association (OCA)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models


class HrWorkerCategory(models.Model):
    """eSocial Table 01 - Worker Categories (Categorias de Trabalhadores).

    Origin / Legal Basis:
    - Official Source: eSocial - Governo Federal do Brasil (MTE, RFB, INSS, CEF)
    - Table: Tabela 01 - Categorias de Trabalhadores
    - Layout Version: eSocial Versão S-1.3 (NT 06/2026 rev., 09/04/2026)
    - Legal Basis: Portaria Conjunta MTP/RFB nº 33/2022, Lei 6.019/74, Lei 10.097/00
    - Official URL: https://www.gov.br/esocial/pt-br/documentacao-tecnica/leiautes-esocial-versao-s-1-3-nt-06-2026-rev-09-04-2026/tabelas.html#01
    - Archival Policy: Expired codes (e.g. 107/108 Verde e Amarelo, 308 Conscrito)
      are preserved with active=False to safeguard historical contracts.
    """

    _name = "hr.worker.category"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Worker Categories"
    _order = "code, name"

    employee_type_default = fields.Selection(
        [
            ("employee", "Employee"),
            ("worker", "Worker"),
            ("student", "Student"),
            ("trainee", "Trainee"),
            ("contractor", "Contractor"),
            ("freelance", "Freelancer"),
        ],
        string="Default Employee Type",
        help="Default employee type associated with this category.",
    )

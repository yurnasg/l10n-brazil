# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class HrEthnicity(models.Model):
    """Ethnicities / Races according to IBGE census categories and eSocial S-2200.

    Origin / Legal Basis:
    - Official Source: Instituto Brasileiro de Geografia e Estatística (IBGE) / eSocial
    - Table / Event: eSocial S-2200 - Campo racaCor
      (1: Branca, 2: Preta, 3: Parda, 4: Amarela, 5: Indígena, 6: Não informado)
    - Layout Version: eSocial Versão S-1.3 (NT 06/2026 rev.)
    - Legal Basis: Metodologia censitária oficial do IBGE.
    """

    _name = "hr.ethnicity"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Ethnicities / Race"

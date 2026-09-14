# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# (c) 2026 Odoo Community Association (OCA)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import _, fields, models
from odoo.exceptions import UserError

OFFICIAL_ESOCIAL_CODES = {
    "physical",
    "hearing",
    "visual",
    "intellectual",
    "mental",
    "rehabilitated",
}


class HrDisability(models.Model):
    """Disability Types for Quota and eSocial Compliance.

    Origin / Legal Basis:
    - Official Source: eSocial / Ministério do Trabalho e Emprego
    - Table / Event: eSocial S-2200 (Cadastramento Inicial e Admissão)
      Fields: defFisica, defVisual, defAuditiva, defMental, defIntelectual, reabReadap
    - Layout Version: eSocial Versão S-1.3 (NT 06/2026 rev.)
    - Legal Basis: Lei nº 8.213/1991 (Art. 93 - Lei de Cotas), Decreto nº 3.298/1999
      (Arts. 3º e 4º), Decreto nº 5.296/2004 e Lei nº 13.146/2015 (Estatuto da PcD).
    - Archival Policy: Official records are protected against unlink; archive via
      active=False if necessary.
    """

    _name = "hr.disability"
    _description = "Disabilities"
    _order = "sequence, name"

    name = fields.Char(required=True, index=True, translate=True)
    code = fields.Char(
        string="Technical Code",
        index=True,
        help="Internal identifier for the disability type.",
    )
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string="Color Index", default=0)

    def unlink(self):
        for record in self:
            if record.code in OFFICIAL_ESOCIAL_CODES:
                raise UserError(
                    _(
                        "Standard disability categories cannot be deleted from "
                        "the system. If you do not wish to use them, you may "
                        "archive them."
                    )
                )
        return super().unlink()

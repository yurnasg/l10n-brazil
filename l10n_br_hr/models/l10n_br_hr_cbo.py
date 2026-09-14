# (c) 2014 Kmee - Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models


class L10nBrHrCbo(models.Model):
    """Brazilian Classification of Occupations (CBO 2002).

    Classificação Brasileira de Ocupações.

    Origin / Legal Basis:
    - Official Source: Ministério do Trabalho e Emprego (MTE)
    - Nomenclature: CBO 2002
    - Structure: 5 hierarchical levels:
      1. Grande Grupo (1 digit)
      2. Subgrupo Principal (2 digits)
      3. Subgrupo (3 digits)
      4. Família (4 digits)
      5. Ocupação / Sinônimo (6 digits)
    - Legal Basis: Portaria MTE nº 397/2002 e atualizações anuais
    - Official URL: http://www.mtecbo.gov.br
    - Archival Policy: Deprecated occupations should be set to active=False.
    """

    _name = "l10n_br_hr.cbo"
    _inherit = "l10n_br_hr.data.abstract"
    _description = "Brazilian Classification of Occupations (CBO 2002 - MTE)"
    _rec_names_search = ("code", "formatted_code", "name", "synonyms")

    parent_id = fields.Many2one(
        comodel_name="l10n_br_hr.cbo",
        string="Parent CBO",
        index=True,
        ondelete="cascade",
    )

    child_ids = fields.One2many(
        comodel_name="l10n_br_hr.cbo",
        inverse_name="parent_id",
        string="Child CBOs",
    )

    internal_type = fields.Selection(
        selection=[
            ("view", "View / Synthetic Group"),
            ("normal", "Normal / Analytical Occupation"),
        ],
        required=True,
        default="normal",
        index=True,
    )

    formatted_code = fields.Char(
        compute="_compute_formatted_code",
        store=True,
        index=True,
    )

    synonyms = fields.Text(
        index=True,
        help="Synonymous and market job titles recognized by MTE for this occupation.",
    )

    @api.depends("code")
    def _compute_formatted_code(self):
        for record in self:
            code = (record.code or "").strip()
            if len(code) == 6:
                record.formatted_code = f"{code[:4]}-{code[4:]}"
            else:
                record.formatted_code = code

    @api.depends("code", "name", "internal_type", "formatted_code")
    def _compute_display_name(self):
        for record in self:
            code_str = record.formatted_code or record.code or ""
            name_str = record.name or ""
            if code_str and name_str:
                record.display_name = f"{code_str} - {name_str}"
            else:
                record.display_name = code_str or name_str

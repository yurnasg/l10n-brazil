# Copyright (C) 2026 - Present Odoo Community Association (OCA)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models
from odoo.osv import expression


class L10nBrIdentityDocumentType(models.Model):
    """Civil identity document types (CIN, RG, CRNM...)."""

    _name = "l10n_br_base.identity.document.type"
    _description = "Identity Document Type"
    _order = "sequence, id"

    name = fields.Char(string="Acronym", required=True, translate=True)
    description = fields.Char(string="Description", translate=True)
    code = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)

    is_cpf_based = fields.Boolean(
        string="Number Is the CPF",
        help="The document number is always the CPF and can't be typed "
        "(used for the CIN).",
    )

    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("code_uniq", "unique(code)", "The document type code must be unique."),
    ]

    @api.model
    def _search_display_name(self, operator, value):
        domain = super()._search_display_name(operator, value)
        if operator in ("ilike", "=ilike", "like", "=like", "=") and isinstance(
            value, str
        ):
            domain = expression.OR(
                [
                    domain,
                    [("name", operator, value)],
                    [("description", operator, value)],
                    [("code", operator, value)],
                ]
            )
        return domain

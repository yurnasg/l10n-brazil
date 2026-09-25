# Copyright (C) 2021  Renato Lima - Akretion
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models


class FormatAddressMixin(models.AbstractModel):
    _inherit = "format.address.mixin"

    def _view_get_address(self, arch):
        """Apply the country address view to every model using this mixin.

        The core only applies the address view of the company's country when
        the view has no model or the same model as the form (the Brazilian
        address view belongs to ``res.partner``). For the other models (e.g.
        ``res.company``) render it here the same way the core does, instead
        of clearing the model of the view in the database: that wrote on
        ``ir.ui.view`` whenever a form was loaded, and the extensions of the
        address view (``l10n_br_zip``) then had to be cleared too, because
        the core only combines extensions of the same model.
        """
        address_view = self.env.company.country_id.address_view_id.sudo()
        if (
            not address_view.model
            or address_view.model == self._name
            or self.env.context.get("no_address_format")
        ):
            return super()._view_get_address(arch)
        Partner = self.env["res.partner"].with_context(no_address_format=True)
        for address_node in arch.xpath("//div[hasclass('o_address_format')]"):
            sub_arch, _sub_view = Partner._get_view(address_view.id, "form")
            # the address view may use fields this model does not have
            try:
                self.env["ir.ui.view"].postprocess_and_fields(
                    sub_arch, model=self._name
                )
            except ValueError:
                return arch
            new_address_node = sub_arch.find('.//div[@class="o_address_format"]')
            if new_address_node is not None:
                sub_arch = new_address_node
            address_node.getparent().replace(address_node, sub_arch)
        return arch

# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.tests import TransactionCase


class L10nBrZipViewsTest(TransactionCase):
    def test_zip_search_button_in_address_forms(self):
        """The zip search button extends the Brazilian address view, which
        is used in the partner and company forms. Loading one form must not
        change the views used by the other one."""
        self.env.company.country_id = self.env.ref("base.br")
        extension = self.env.ref("l10n_br_zip.l10n_br_zip_res_partner_form")
        self.env.registry.clear_cache("templates")
        for model in ("res.company", "res.partner", "res.company"):
            with self.subTest(model=model):
                arch = self.env[model].get_view(view_type="form")["arch"]
                self.assertIn('name="zip_search"', arch)
        extension.invalidate_recordset(["model"])
        self.assertEqual(extension.model, "res.partner")

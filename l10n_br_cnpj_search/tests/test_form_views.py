# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from lxml import etree

from odoo.tests import Form, tagged

from odoo.addons.l10n_br_cnpj_search.tests.common import TestCnpjCommon

CNPJ = "14500536000180"
CNPJ_FORMATTED = "14.500.536/0001-80"
FOREIGN_VAT = "12-3456789"


@tagged("post_install", "-at_install")
class TestCnpjSearchFormViews(TestCnpjCommon):
    """l10n_br_base shows Brazilian records their formatted CNPJ
    (vat_formatted_cnpj) and foreign records their vat. The search button
    goes next to the formatted CNPJ, and the vat keeps its visibility."""

    def _search_button(self, model):
        arch = etree.fromstring(self.env[model].get_view(view_type="form")["arch"])
        [button] = arch.xpath("//button[@name='action_open_cnpj_search_wizard']")
        return button

    def test_partner_search_button_next_to_formatted_cnpj(self):
        """Brazilian companies only: a CNPJ is not searched for a person (CPF)
        or a foreign company."""
        button = self._search_button("res.partner")
        row = button.getparent()
        self.assertEqual(row.xpath("field/@name"), ["vat_formatted_cnpj"])
        self.assertEqual(row.get("invisible"), "not show_l10n_br")
        self.assertEqual(button.get("invisible"), "not is_company")

    def test_company_search_button_next_to_formatted_cnpj(self):
        row = self._search_button("res.company").getparent()
        self.assertEqual(row.xpath("field/@name"), ["vat_formatted_cnpj"])
        self.assertEqual(row.get("invisible"), "not show_l10n_br")

    def test_br_partner_shows_cnpj_once(self):
        partner_form = Form(self.model)
        partner_form.company_type = "company"
        partner_form.name = "BR Company"
        partner_form.country_id = self.env.ref("base.br")
        with self.assertRaises(AssertionError):
            partner_form.vat = CNPJ
        partner_form.vat_formatted_cnpj = CNPJ_FORMATTED
        self.assertEqual(partner_form.save().vat, CNPJ)

    def test_br_company_shows_cnpj_once(self):
        company_form = Form(self.env["res.company"])
        company_form.name = "BR Company"
        company_form.country_id = self.env.ref("base.br")
        with self.assertRaises(AssertionError):
            company_form.vat = CNPJ
        company_form.vat_formatted_cnpj = CNPJ_FORMATTED
        self.assertEqual(company_form.save().vat, CNPJ)

    def test_foreign_partner_keeps_vat(self):
        partner_form = Form(self.model)
        partner_form.company_type = "company"
        partner_form.name = "US Company"
        partner_form.country_id = self.env.ref("base.us")
        partner_form.vat = FOREIGN_VAT
        with self.assertRaises(AssertionError):
            partner_form.vat_formatted_cnpj = CNPJ_FORMATTED
        self.assertEqual(partner_form.save().vat, FOREIGN_VAT)

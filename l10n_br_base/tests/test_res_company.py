# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


from .common import (
    CNPJ_1,
    CNPJ_1_FORMATTED,
    IE_SP,
    LONG_DISTRICT,
    LONG_LEGAL_NAME,
    L10nBrBaseCase,
)


class CompanyTest(L10nBrBaseCase):
    def _br_company(self, **vals):
        return self.env["res.company"].create(
            dict({"name": "Test BR Company", "country_id": self.br.id}, **vals)
        )

    def test_company_fields_written_on_partner(self):
        company = self._br_company(state_id=self.state_sp.id)
        company.write(
            {
                "legal_name": "Test BR Company Ltda",
                "district": "Centro",
                "street_name": "Avenida Paulista",
                "street_number": "807",
                "street_number2": "CJ 2315",
                "city_id": self.city_sp.id,
                "l10n_br_ie_code": IE_SP,
            }
        )
        partner = company.partner_id
        self.assertEqual(partner.legal_name, "Test BR Company Ltda")
        self.assertEqual(partner.district, "Centro")
        self.assertEqual(partner.street_name, "Avenida Paulista")
        self.assertEqual(partner.street_number, "807")
        self.assertEqual(partner.street_number2, "CJ 2315")
        self.assertEqual(partner.city_id, self.city_sp)
        self.assertEqual(partner.state_id, self.state_sp)
        self.assertEqual(partner.l10n_br_ie_code, IE_SP)

    def test_long_legal_name_and_district_kept(self):
        company = self._br_company(legal_name=LONG_LEGAL_NAME, district=LONG_DISTRICT)
        company.invalidate_recordset(["legal_name", "district"])
        self.assertEqual(company.legal_name, LONG_LEGAL_NAME)
        self.assertEqual(company.district, LONG_DISTRICT)
        self.assertEqual(company.partner_id.legal_name, LONG_LEGAL_NAME)
        self.assertEqual(company.partner_id.district, LONG_DISTRICT)

    def test_company_vat_unformatted(self):
        company = self._br_company(vat=CNPJ_1_FORMATTED)
        self.assertEqual(company.vat, CNPJ_1)
        self.assertEqual(company.partner_id.vat, CNPJ_1)

    def test_company_onchange_state_clears_ie(self):
        company = self.env["res.company"].new(
            {
                "name": "Draft Company",
                "country_id": self.br.id,
                "state_id": self.state_rj.id,
                "l10n_br_ie_code": IE_SP,
            }
        )
        company._onchange_state_id()
        self.assertFalse(company.l10n_br_ie_code)

    def test_form_views_load(self):
        company_arch = self.env["res.company"].get_view(view_type="form")["arch"]
        self.assertIn("l10n_br_ie_code", company_arch)
        partner_arch = self.partner_model.get_view(view_type="form")["arch"]
        for field_name in ("legal_name", "vat_formatted_cnpj", "l10n_br_ie_code"):
            self.assertIn(field_name, partner_arch)

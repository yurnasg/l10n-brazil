# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo.exceptions import ValidationError
from odoo.tests import Form, TransactionCase


class ResPartnerTest(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner_model = cls.env["res.partner"]
        cls.br = cls.env.ref("base.br")
        cls.us = cls.env.ref("base.us")
        cls.doc_type_cin = cls.env.ref("l10n_br_base.identity_doc_type_cin")
        cls.doc_type_rg = cls.env.ref("l10n_br_base.identity_doc_type_rg")

    def _create_person(self, **vals):
        return self.partner_model.create(
            dict({"name": "Person", "country_id": self.br.id}, **vals)
        )

    def test_cin_number_follows_cpf(self):
        partner = self._create_person(
            vat="529.982.247-25", l10n_br_identity_doc_type=self.doc_type_cin.id
        )
        self.assertEqual(partner.l10n_br_rg_code, "52998224725")
        partner.vat = "111.444.777-35"
        self.assertEqual(partner.l10n_br_rg_code, "11144477735")

    def test_rg_number_kept_on_cpf_change(self):
        partner = self._create_person(
            vat="52998224725",
            l10n_br_identity_doc_type=self.doc_type_rg.id,
            l10n_br_rg_code="12.345.678-9",
        )
        partner.vat = "11144477735"
        self.assertEqual(partner.l10n_br_rg_code, "12.345.678-9")

    def test_identity_doc_type_search_by_name_and_acronym(self):
        doc_type_model = self.env["l10n_br_base.identity.document.type"]
        # Search by acronym
        res_rg = doc_type_model.name_search("RG")
        rg_ids = [r[0] for r in res_rg]
        self.assertIn(self.doc_type_rg.id, rg_ids)
        # Search by full name / description
        res_rg_desc = doc_type_model.name_search("General Registry")
        rg_desc_ids = [r[0] for r in res_rg_desc]
        self.assertIn(self.doc_type_rg.id, rg_desc_ids)

    def test_number_without_document_type_kept_on_cpf_change(self):
        """Partners registered before the document type existed keep their
        number."""
        partner = self._create_person(vat="52998224725", l10n_br_rg_code="12.345.678-9")
        partner.vat = "11144477735"
        self.assertEqual(partner.l10n_br_rg_code, "12.345.678-9")

    def test_switch_document_type(self):
        partner = self._create_person(
            vat="52998224725",
            l10n_br_identity_doc_type=self.doc_type_rg.id,
            l10n_br_rg_code="12.345.678-9",
        )
        partner.l10n_br_identity_doc_type = self.doc_type_cin
        self.assertEqual(partner.l10n_br_rg_code, "52998224725")
        # leaving the CIN drops the copied CPF so the new number can be typed
        partner.l10n_br_identity_doc_type = self.doc_type_rg
        self.assertFalse(partner.l10n_br_rg_code)
        partner.l10n_br_rg_code = "98.765.432-1"
        self.assertEqual(partner.l10n_br_rg_code, "98.765.432-1")

    def test_cin_number_in_partner_form(self):
        partner = self._create_person(vat="52998224725")
        with Form(partner) as partner_form:
            partner_form.l10n_br_identity_doc_type = self.doc_type_cin
            self.assertEqual(partner_form.l10n_br_rg_code, "52998224725")
        self.assertEqual(partner.l10n_br_rg_code, "52998224725")

    def test_br_vat_editable_in_partner_form(self):
        """The partner form hides vat for Brazilian partners and shows
        vat_formatted_cnpj instead, so that field must be editable."""
        partner_form = Form(self.partner_model)
        partner_form.name = "Form Person"
        partner_form.country_id = self.br
        partner_form.l10n_br_identity_doc_type = self.doc_type_cin
        partner_form.vat_formatted_cnpj = "063.109.997-29"
        self.assertEqual(partner_form.l10n_br_rg_code, "06310999729")
        partner = partner_form.save()
        self.assertEqual(partner.vat, "06310999729")
        self.assertEqual(partner.vat_formatted_cnpj, "063.109.997-29")
        self.assertEqual(partner.l10n_br_rg_code, "06310999729")

    def test_br_vat_editable_in_company_form(self):
        company_form = Form(self.env["res.company"])
        company_form.name = "Form Company"
        company_form.country_id = self.br
        company_form.vat_formatted_cnpj = "14.500.536/0001-80"
        company = company_form.save()
        self.assertEqual(company.vat, "14500536000180")
        self.assertEqual(company.partner_id.vat, "14500536000180")

    def test_name_search_masked_cnpj_and_cpf(self):
        """The CNPJ/CPF typed with mask in a many2one finds the partner."""
        company = self.partner_model.create(
            {
                "name": "Masked Search Company",
                "is_company": True,
                "country_id": self.br.id,
                "vat": "14.500.536/0001-80",
            }
        )
        person = self._create_person(name="Masked Search Person", vat="063.109.997-29")

        def found(text):
            return [res[0] for res in self.partner_model.name_search(text)]

        self.assertIn(company.id, found("14.500.536/0001-80"))
        self.assertIn(company.id, found("14.500.536"))
        self.assertIn(person.id, found("063.109.997-29"))
        self.assertEqual(
            self.partner_model.search([("display_name", "ilike", "063.109.997-29")]),
            person,
        )

    def test_copy_multi_br_partners(self):
        """Copying several Brazilian partners at once must work and must not
        duplicate the CPF/CNPJ."""
        partners = self.partner_model.create(
            [
                {"name": "Person 1", "country_id": self.br.id, "vat": "52998224725"},
                {"name": "Person 2", "country_id": self.br.id, "vat": "11144477735"},
            ]
        )
        copies = partners.copy()
        self.assertEqual(len(copies), 2)
        self.assertFalse(any(copies.mapped("vat")))

    def test_copy_single_br_partner_clears_vat(self):
        partner = self.partner_model.create(
            {"name": "Person", "country_id": self.br.id, "vat": "52998224725"}
        )
        self.assertFalse(partner.copy().vat)

    def test_write_multi_foreign_partners_keeps_vat_format(self):
        """Writing the VAT on several foreign partners must not strip its
        punctuation just because the current company is Brazilian."""
        self.env.company.country_id = self.br
        partners = self.partner_model.create(
            [
                {"name": "US Co 1", "is_company": True, "country_id": self.us.id},
                {"name": "US Co 2", "is_company": True, "country_id": self.us.id},
            ]
        )
        partners.write({"vat": "12-3456789"})
        self.assertEqual(partners.mapped("vat"), ["12-3456789", "12-3456789"])

    def test_write_multi_mixed_countries_vat_format(self):
        """With Brazilian and foreign partners in the same write, only the
        Brazilian ones get the VAT unformatted."""
        br_partner, us_partner = self.partner_model.create(
            [
                {"name": "BR Person", "country_id": self.br.id},
                {"name": "US Person", "country_id": self.us.id},
            ]
        )
        (br_partner | us_partner).write({"vat": "529.982.247-25"})
        self.assertEqual(br_partner.vat, "52998224725")
        self.assertEqual(us_partner.vat, "529.982.247-25")

    def test_write_single_foreign_partner_keeps_vat_format(self):
        self.env.company.country_id = self.br
        partner = self.partner_model.create(
            {"name": "US Co", "is_company": True, "country_id": self.us.id}
        )
        partner.write({"vat": "12-3456789"})
        self.assertEqual(partner.vat, "12-3456789")

    def test_commercial_sync_only_changed_fields(self):
        """Like the base method, only the commercial fields that were written
        on the parent must be propagated to the children."""
        industry_parent, industry_child = self.env["res.partner.industry"].create(
            [{"name": "Industry Parent"}, {"name": "Industry Child"}]
        )
        company = self.partner_model.create(
            {
                "name": "BR Company",
                "is_company": True,
                "country_id": self.br.id,
                "industry_id": industry_parent.id,
            }
        )
        child = self.partner_model.create(
            {"name": "Contact", "parent_id": company.id, "country_id": self.br.id}
        )
        child.industry_id = industry_child
        company.write({"company_registry": "REG-123"})
        self.assertEqual(child.company_registry, "REG-123")
        self.assertEqual(child.industry_id, industry_child)

    def test_other_ie_duplicated_on_another_partner(self):
        """An 'other State Tax Number' already used by another partner (also as
        an other State Tax Number) must be rejected."""
        partner_model = self.partner_model.with_context(disable_ie_validation=True)
        ba = self.env.ref("base.state_br_ba")
        vals = {"is_company": True, "country_id": self.br.id}
        partner_model.create(
            dict(
                vals,
                name="Company SP",
                state_id=self.env.ref("base.state_br_sp").id,
                state_tax_number_ids=[
                    (0, 0, {"state_id": ba.id, "l10n_br_ie_code": "41902653"})
                ],
            )
        )
        other = partner_model.create(
            dict(vals, name="Company RJ", state_id=self.env.ref("base.state_br_rj").id)
        )
        with self.assertRaises(ValidationError):
            other.write(
                {
                    "state_tax_number_ids": [
                        (0, 0, {"state_id": ba.id, "l10n_br_ie_code": "41902653"})
                    ]
                }
            )

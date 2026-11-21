# Copyright (C) 2026 - Present Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.tests import Form, TransactionCase


class TestIdentityDocument(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        cls.partner_model = cls.env["res.partner"]
        cls.br = cls.env.ref("base.br")
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
        res_rg = doc_type_model.name_search("RG")
        rg_ids = [r[0] for r in res_rg]
        self.assertIn(self.doc_type_rg.id, rg_ids)
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

    def test_identity_document_visibility(self):
        """Visible for Brazilian individuals and for foreign individuals in a
        Brazilian company (CRNM / NF-e idEstrangeiro), hidden when both the
        company and the individual are foreign or on companies."""
        us = self.env.ref("base.us")
        us_company = self.env["res.company"].create(
            {"name": "US Company", "country_id": us.id}
        )
        br_company = self.env["res.company"].create(
            {"name": "BR Company", "country_id": self.br.id}
        )
        foreign_person = self.partner_model.create(
            {"name": "Foreign Person", "country_id": us.id}
        )
        br_person = self._create_person(name="BR Person")
        br_company_partner = self._create_person(name="BR Corp", is_company=True)

        # Foreign person in a US company: hidden
        with Form(foreign_person.with_company(us_company)) as form:
            self.assertTrue(form._get_modifier("l10n_br_rg_code", "invisible"))

        # Foreign person in a BR company: visible
        with Form(foreign_person.with_company(br_company)) as form:
            self.assertFalse(form._get_modifier("l10n_br_rg_code", "invisible"))

        # Brazilian person in a US company: visible
        with Form(br_person.with_company(us_company)) as form:
            self.assertFalse(form._get_modifier("l10n_br_rg_code", "invisible"))

        # Company: hidden
        with Form(br_company_partner.with_company(br_company)) as form:
            self.assertTrue(form._get_modifier("l10n_br_rg_code", "invisible"))

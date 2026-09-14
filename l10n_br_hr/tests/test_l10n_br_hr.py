from dateutil.relativedelta import relativedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
from odoo.tests import Form, TransactionCase
from odoo.tests.common import new_test_user

from ..hooks import post_init_hook


class TestL10nBr(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.company.country_id = cls.env.ref("base.br")

        cls.disability_physical = cls.env.ref("l10n_br_hr.disability_physical")
        cls.disability_visual = cls.env.ref("l10n_br_hr.disability_visual")
        cls.disability_multiple_legacy = cls.env.ref(
            "l10n_br_hr.disability_multiple_legacy"
        )
        cls.disability_intellectual_mental_legacy = cls.env.ref(
            "l10n_br_hr.disability_intellectual_mental_legacy"
        )

        cls.doc_type_cin = cls.env.ref("l10n_br_base.identity_doc_type_cin")
        cls.doc_type_rg = cls.env.ref("l10n_br_base.identity_doc_type_rg")
        cls.doc_type_crnm = cls.env.ref("l10n_br_base.identity_doc_type_crnm")

        cls.employee = cls.env["hr.employee"].create(
            {
                "address_id": cls.env["res.partner"].search([]).company_id.id,
                "company_id": cls.env["res.partner"].search([]).company_id.id,
                "department_id": cls.env["hr.department"],
                "civil_certificate_type_id": cls.env["hr.civil.certificate.type"],
                "disability_ids": [(6, 0, [cls.disability_physical.id])],
                "is_disability_quota": True,
                "disability_notes": "Right hand index finger limitation",
                "name": "l10n brazil demo employee",
                "pis_pasep": "496.85994.95-6",
                "vat": "853.334.271-35",
                "country_id": cls.env.ref("base.br").id,
            }
        )

        cls.assertTrue(cls.employee, "Error on create a l10n_br employee")

    def test_invalid_hr_employee_vat(self):
        with self.assertRaises(ValidationError):
            self.employee.write({"vat": "853.334.271-351"})

    def test_vat_and_cpf_fields(self):
        # Writing formatted vat normalizes to unformatted digits in DB
        self.employee.write({"vat": "780.048.630-35"})
        self.assertEqual(self.employee.vat, "78004863035")
        self.assertEqual(self.employee.cpf, "78004863035")

        # Writing via cpf alias also updates vat and partner vat
        self.employee.write({"cpf": "85333427135"})
        self.assertEqual(self.employee.vat, "85333427135")
        self.assertEqual(self.employee.work_contact_id.vat, "85333427135")

    def test_pis_pasep_sanitization(self):
        self.employee.write({"pis_pasep": "120.50901.12-9"})
        self.assertEqual(self.employee.pis_pasep, "12050901129")

    def test_invalid_employee_pis_pasep(self):
        with self.assertRaises(ValidationError):
            self.employee.write({"pis_pasep": "496.851994.95-6"})

    def test_l10n_br_hr_cbo(self):
        cbo = self.env.ref("l10n_br_hr.cbo_010105")
        self.assertTrue(cbo.active)
        self.assertEqual(cbo.code, "010105")
        self.assertEqual(cbo.formatted_code, "0101-05")
        self.assertEqual(cbo.internal_type, "normal")
        self.assertEqual(cbo.display_name, "0101-05 - Oficial general da aeronáutica")

        # Test hierarchy relation to family
        cbo_dev = self.env.ref("l10n_br_hr.cbo_212405")
        self.assertEqual(cbo_dev.formatted_code, "2124-05")
        self.assertEqual(cbo_dev.parent_id.code, "2124")
        self.assertEqual(cbo_dev.parent_id.internal_type, "view")
        self.assertIn("Desenvolvedor de ti", cbo_dev.synonyms)

        # Test search by synonym
        search_res = self.env["l10n_br_hr.cbo"].name_search("Desenvolvedor de ti")
        found_ids = [r[0] for r in search_res]
        self.assertIn(cbo_dev.id, found_ids)

        # Test archiving CBO
        cbo.write({"active": False})
        self.assertFalse(cbo.active)

    def test_hr_disability_data(self):
        self.assertEqual(self.disability_physical.name, "Physical disability")
        self.assertEqual(self.disability_physical.code, "physical")
        self.assertEqual(self.disability_physical.sequence, 10)
        self.assertEqual(self.disability_physical.color, 4)
        self.assertTrue(self.disability_physical.active)
        self.assertEqual(self.disability_multiple_legacy.name, "Multiple")
        self.assertEqual(self.disability_multiple_legacy.sequence, 100)
        self.assertEqual(self.disability_multiple_legacy.color, 1)
        self.assertFalse(self.disability_multiple_legacy.active)
        self.assertEqual(
            self.disability_intellectual_mental_legacy.name,
            "Intellectual / Mental",
        )
        self.assertEqual(self.disability_intellectual_mental_legacy.color, 1)
        self.assertFalse(self.disability_intellectual_mental_legacy.active)

    def test_hr_disability_unlink_protection(self):
        # Official eSocial records cannot be deleted
        with self.assertRaises(UserError):
            self.disability_physical.unlink()

    def test_hr_disability_esocial_validation(self):
        # eSocial Rule 1722: infoCota=True without disability raises ValidationError
        with self.assertRaises(ValidationError):
            self.employee.write(
                {"disability_ids": [(5, 0, 0)], "is_disability_quota": True}
            )

    def test_has_legacy_disability(self):
        # Test Multiple legacy detection & visibility of archived tags
        self.employee.write(
            {"disability_ids": [(6, 0, [self.disability_multiple_legacy.id])]}
        )
        self.assertTrue(self.employee.has_legacy_disability)
        self.assertIn(self.disability_multiple_legacy, self.employee.disability_ids)

        # Test Intellectual/Mental legacy detection & visibility
        self.employee.write(
            {
                "disability_ids": [
                    (6, 0, [self.disability_intellectual_mental_legacy.id])
                ]
            }
        )
        self.assertTrue(self.employee.has_legacy_disability)
        self.assertIn(
            self.disability_intellectual_mental_legacy, self.employee.disability_ids
        )

        # Test arbitrary custom legacy tag from past database
        custom_disability = self.env["hr.disability"].create(
            {"name": "Custom Dwarfism", "code": "custom_7", "active": False}
        )
        self.employee.write({"disability_ids": [(6, 0, [custom_disability.id])]})
        self.assertTrue(self.employee.has_legacy_disability)
        self.assertIn(custom_disability, self.employee.disability_ids)

        # Test modern records do not trigger legacy warning
        self.employee.write({"disability_ids": [(6, 0, [self.disability_physical.id])]})
        self.assertFalse(self.employee.has_legacy_disability)

    def test_hr_ethnicity(self):
        ethnicity_1 = self.env.ref("l10n_br_hr.ethnicity_1")
        self.assertEqual(ethnicity_1.name, "White")
        self.assertEqual(ethnicity_1.code, "1")
        self.assertEqual(ethnicity_1.display_name, "1 - White")

    def test_esocial_worker_category(self):
        cat_101 = self.env.ref("l10n_br_hr.worker_category_101")
        self.assertEqual(cat_101.code, "101")
        self.assertEqual(cat_101.name, "General Employee - CLT Indeterminate")
        self.assertEqual(
            cat_101.display_name, "101 - General Employee - CLT Indeterminate"
        )

        cat_901 = self.env.ref("l10n_br_hr.worker_category_901")
        self.assertEqual(cat_901.code, "901")
        self.assertEqual(cat_901.employee_type_default, "student")

        cat_103 = self.env.ref("l10n_br_hr.worker_category_103")
        self.assertEqual(cat_103.code, "103")
        self.assertEqual(cat_103.employee_type_default, "trainee")

        # Test onchange from category sets employee_type
        self.employee.worker_category_id = cat_901
        self.employee._onchange_worker_category_id()
        self.assertEqual(self.employee.employee_type, "student")

        self.employee.worker_category_id = cat_103
        self.employee._onchange_worker_category_id()
        self.assertEqual(self.employee.employee_type, "trainee")

    def test_contractor_partner(self):
        vendor = self.env["res.partner"].create(
            {"name": "Terceirização e Serviços Ltda", "is_company": True}
        )
        self.employee.write(
            {
                "employee_type": "contractor",
                "contractor_partner_id": vendor.id,
            }
        )
        self.assertEqual(self.employee.contractor_partner_id, vendor)

    def test_employee_relative_esocial(self):
        relation_child = self.env.ref("hr_employee_relative.relation_child")
        relative = self.env["hr.employee.relative"].create(
            {
                "employee_id": self.employee.id,
                "relation_id": relation_child.id,
                "name": "Maria Silva",
                "dependent_type": "03",
                "vat": "111.444.777-35",
                "is_irrf_dependent": True,
                "is_family_allowance_dependent": True,
                "is_incapable": False,
            }
        )
        self.assertEqual(relative.dependent_type, "03")
        self.assertTrue(relative.is_irrf_dependent)
        self.assertTrue(relative.is_family_allowance_dependent)
        self.assertFalse(relative.is_incapable)

        # Test normalization
        self.assertEqual(relative.vat, "11144477735")

        # Test partner_id onchange populates vat
        partner = self.env["res.partner"].create(
            {
                "name": "Joãozinho Silva",
                "vat": "52998224725",
                "country_id": self.env.ref("base.br").id,
            }
        )
        relative.partner_id = partner
        relative._onchange_partner_id()
        self.assertEqual(relative.vat, "52998224725")

        # Test invalid CPF validation
        with self.assertRaises(ValidationError):
            relative.write({"vat": "123.456.789-00"})

    def test_employee_relative_auto_sync_native_esocial(self):
        relation_child = self.env.ref("hr_employee_relative.relation_child")
        relation_spouse = self.env.ref("hr_employee_relative.relation_spouse")

        # 1. Test onchange relation_id sets dependent_type
        relative = self.env["hr.employee.relative"].new(
            {
                "employee_id": self.employee.id,
                "name": "Pedrinho",
                "relation_id": relation_child.id,
            }
        )
        relative._onchange_relation_id()
        self.assertEqual(relative.dependent_type, "03")

        # 2. Test child under 14 auto-sets family allowance and IRRF
        today = fields.Date.today()
        relative.date_of_birth = today - relativedelta(years=8)
        relative._onchange_dependent_rules()
        self.assertTrue(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

        # 3. Test child of 16 years: no family allowance, but IRRF dependent
        relative.date_of_birth = today - relativedelta(years=16)
        relative._onchange_dependent_rules()
        self.assertFalse(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

        # 4. Test child of 22 years (not university): neither
        relative.date_of_birth = today - relativedelta(years=22)
        relative._onchange_dependent_rules()
        self.assertFalse(relative.is_family_allowance_dependent)
        self.assertFalse(relative.is_irrf_dependent)

        # 5. Test child of 22 years at university: IRRF dependent
        relative.is_student = True
        relative._onchange_dependent_rules()
        self.assertTrue(relative.is_irrf_dependent)

        # 6. Test child with disability/incapable: both True regardless of age
        relative.is_incapable = True
        relative._onchange_dependent_rules()
        self.assertTrue(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

        # 7. Test spouse sets dependent_type 01, IRRF True, Family Allowance False
        relative.is_incapable = False
        relative.relation_id = relation_spouse.id
        relative._onchange_relation_id()
        self.assertEqual(relative.dependent_type, "01")
        self.assertTrue(relative.is_irrf_dependent)
        self.assertFalse(relative.is_family_allowance_dependent)

    def test_education_level_sync(self):
        # 1. Onchange education_level -> certificate
        self.employee.education_level = "09"
        self.employee._onchange_education_level()
        self.assertEqual(self.employee.certificate, "bachelor")

        self.employee.education_level = "11"
        self.employee._onchange_education_level()
        self.assertEqual(self.employee.certificate, "master")

        self.employee.education_level = "05"
        self.employee._onchange_education_level()
        self.assertEqual(self.employee.certificate, "other")

        # 2. Onchange certificate -> education_level
        self.employee.certificate = "doctor"
        self.employee._onchange_certificate()
        self.assertEqual(self.employee.education_level, "12")

    def test_legacy_printed_documents_optional_and_historical(self):
        # 1. Verify employee created in setUpClass has no legacy printed docs
        # and no default category values
        self.assertFalse(self.employee.ctps)
        self.assertFalse(self.employee.ctps_series)
        self.assertFalse(self.employee.ctps_date)
        self.assertFalse(self.employee.ctps_uf_id)
        self.assertFalse(self.employee.creservist)
        self.assertFalse(self.employee.cresv_categ)
        self.assertFalse(self.employee.voter_title)
        self.assertFalse(self.employee.voter_zone)
        self.assertFalse(self.employee.voter_section)

        # 2. Creating a new employee without any legacy documents succeeds without error
        new_emp = self.env["hr.employee"].create(
            {
                "name": "Employee Without Legacy Docs",
                "vat": "780.048.630-35",
            }
        )
        self.assertTrue(new_emp)
        self.assertFalse(new_emp.ctps)
        self.assertFalse(new_emp.creservist)
        self.assertFalse(new_emp.cresv_categ)
        self.assertFalse(new_emp.voter_title)

        # 3. Writing historical values succeeds and preserves records
        state_sp = self.env.ref("base.state_br_sp")
        new_emp.write(
            {
                "ctps": "1234567",
                "ctps_series": "0010",
                "ctps_date": "2015-05-10",
                "ctps_uf_id": state_sp.id,
                "creservist": "987654321",
                "cresv_categ": "1",
                "voter_title": "123456780123",
                "voter_zone": "001",
                "voter_section": "0042",
            }
        )
        self.assertEqual(new_emp.ctps, "1234567")
        self.assertEqual(new_emp.ctps_series, "0010")
        self.assertEqual(str(new_emp.ctps_date), "2015-05-10")
        self.assertEqual(new_emp.ctps_uf_id, state_sp)
        self.assertEqual(new_emp.creservist, "987654321")
        self.assertEqual(new_emp.cresv_categ, "1")
        self.assertEqual(new_emp.voter_title, "123456780123")
        self.assertEqual(new_emp.voter_zone, "001")
        self.assertEqual(new_emp.voter_section, "0042")

    def test_hr_identity_type_one2many_relation(self):
        id_type = self.env["hr.identity.type"].create(
            {"name": "Registro Geral", "initials": "RG"}
        )
        self.assertEqual(id_type.name, "Registro Geral")
        self.assertEqual(id_type.initials, "RG")
        self.assertFalse(id_type.employee_ids)

        self.employee.write({"identity_type_id": id_type.id})
        self.assertIn(self.employee, id_type.employee_ids)

    def test_hr_employee_relative_vat_sanitization(self):
        rel_child = self.env.ref("hr_employee_relative.relation_child")
        relative = self.env["hr.employee.relative"].create(
            {
                "name": "Filho Demo",
                "employee_id": self.employee.id,
                "relation_id": rel_child.id,
                "vat": "780.048.630-35",
            }
        )
        self.assertEqual(relative.vat, "78004863035")

        relative.write({"vat": "853.334.271-35"})
        self.assertEqual(relative.vat, "85333427135")

    def test_hr_employee_relative_vat_invalid(self):
        rel_child = self.env.ref("hr_employee_relative.relation_child")
        # Invalid CPF digits
        with self.assertRaises(ValidationError):
            self.env["hr.employee.relative"].create(
                {
                    "name": "Filho Invalido",
                    "employee_id": self.employee.id,
                    "relation_id": rel_child.id,
                    "vat": "123.456.789-00",
                }
            )

    def test_hr_employee_relative_vat_reject_cnpj(self):
        rel_child = self.env.ref("hr_employee_relative.relation_child")
        # CNPJ must not be accepted for a physical dependent
        with self.assertRaises(ValidationError):
            self.env["hr.employee.relative"].create(
                {
                    "name": "Dependente CNPJ",
                    "employee_id": self.employee.id,
                    "relation_id": rel_child.id,
                    "vat": "62.228.384/0001-51",
                }
            )

    def test_hr_employee_relative_rules_automation(self):
        rel_child = self.env.ref("hr_employee_relative.relation_child")
        today = fields.Date.today()
        relative = self.env["hr.employee.relative"].create(
            {
                "name": "Filho Regras",
                "employee_id": self.employee.id,
                "relation_id": rel_child.id,
                "date_of_birth": today - relativedelta(years=8),
                "vat": "529.982.247-25",
            }
        )
        # Child under 14: family allowance and IRRF
        relative._onchange_relation_id()
        self.assertEqual(relative.dependent_type, "03")
        self.assertTrue(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

        # Child aged 16: no family allowance, but IRRF eligible
        relative.date_of_birth = today - relativedelta(years=16)
        relative._onchange_dependent_rules()
        self.assertFalse(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

        # Child aged 23 non-student: no family allowance, no IRRF
        relative.date_of_birth = today - relativedelta(years=23)
        relative._onchange_dependent_rules()
        self.assertFalse(relative.is_family_allowance_dependent)
        self.assertFalse(relative.is_irrf_dependent)

        # Child aged 23 student: IRRF eligible
        relative.is_student = True
        relative._onchange_dependent_rules()
        self.assertFalse(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

        # Incapable: always eligible for both
        relative.is_incapable = True
        relative._onchange_dependent_rules()
        self.assertTrue(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

    def test_dependent_student_and_ended_types(self):
        """Since 25/04/2023 a student child is type 03 with the student flag;
        types 04 and 07 are kept only on existing dependents."""
        rel_child = self.env.ref("hr_employee_relative.relation_child")
        relative = self.env["hr.employee.relative"].create(
            {
                "name": "Dependente Universitário",
                "employee_id": self.employee.id,
                "relation_id": rel_child.id,
                "dependent_type": "10",
                "date_of_birth": fields.Date.today() - relativedelta(years=23),
                "is_student": True,
                "vat": "529.982.247-25",
            }
        )
        # the student extension applies only to children and siblings
        relative._onchange_dependent_rules()
        self.assertFalse(relative.is_irrf_dependent)
        relative.dependent_type = "06"
        relative._onchange_dependent_rules()
        self.assertTrue(relative.is_irrf_dependent)

        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            relative.write({"dependent_type": "04"})

        # an existing dependent with an ended type can still be edited
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE hr_employee_relative SET dependent_type = '07' WHERE id = %s",
            (relative.id,),
        )
        relative.invalidate_recordset()
        relative.write({"name": "Dependente Universitário (histórico)"})
        self.assertEqual(relative.dependent_type, "07")
        relative._onchange_dependent_rules()
        self.assertTrue(relative.is_irrf_dependent)

    def test_job_cbo_is_archived(self):
        cbo = self.env.ref("l10n_br_hr.cbo_010105")
        cbo.write({"active": True})
        job = self.env["hr.job"].create(
            {
                "name": "Oficial da Aeronautica",
                "cbo_id": cbo.id,
            }
        )
        self.assertFalse(job.cbo_is_archived)

        cbo.write({"active": False})
        self.assertTrue(job.cbo_is_archived)

        job.write({"cbo_id": False})
        self.assertFalse(job.cbo_is_archived)

    def test_post_init_hook_worker_category(self):
        employees = self.env["hr.employee"].create(
            [
                {"name": "Hook Regular Employee", "employee_type": "employee"},
                {"name": "Hook Freelance Employee", "employee_type": "freelance"},
                {"name": "Hook Contractor Employee", "employee_type": "contractor"},
            ]
        )
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE hr_employee SET worker_category_id = NULL WHERE id IN %s",
            (tuple(employees.ids),),
        )
        post_init_hook(self.env)
        employees.invalidate_recordset()

        self.assertEqual(
            employees[0].worker_category_id,
            self.env.ref("l10n_br_hr.worker_category_101"),
        )
        self.assertEqual(
            employees[1].worker_category_id,
            self.env.ref("l10n_br_hr.worker_category_701"),
        )
        self.assertFalse(employees[2].worker_category_id)

    def test_employee_relative_age_year_fallback(self):
        rel_child = self.env.ref("hr_employee_relative.relation_child")
        relative = self.env["hr.employee.relative"].new(
            {
                "employee_id": self.employee.id,
                "name": "Filho Sem Data Nasc",
                "relation_id": rel_child.id,
                "date_of_birth": False,
                "age_year": 10,
            }
        )
        relative._onchange_relation_id()
        self.assertTrue(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

        relative.age_year = 20
        relative._onchange_dependent_rules()
        self.assertFalse(relative.is_family_allowance_dependent)
        self.assertTrue(relative.is_irrf_dependent)

        relative.age_year = 23
        relative._onchange_dependent_rules()
        self.assertFalse(relative.is_family_allowance_dependent)
        self.assertFalse(relative.is_irrf_dependent)

    def test_employee_relative_vat_invalid_length(self):
        rel_child = self.env.ref("hr_employee_relative.relation_child")
        with self.assertRaises(ValidationError):
            self.env["hr.employee.relative"].create(
                {
                    "name": "Filho CPF Curto",
                    "employee_id": self.employee.id,
                    "relation_id": rel_child.id,
                    "vat": "12345",
                }
            )

    def test_employee_batch_normalization(self):
        employees = self.env["hr.employee"].create(
            [
                {
                    "name": "Batch Employee 1",
                    "vat": "000.001.000-64",
                    "pis_pasep": "496.85994.95-6",
                },
                {
                    "name": "Batch Employee 2",
                    "vat": "000.001.001-45",
                    "pis_pasep": "120.50901.12-9",
                },
            ]
        )
        self.assertEqual(employees[0].vat, "00000100064")
        self.assertEqual(employees[0].pis_pasep, "49685994956")
        self.assertEqual(employees[1].vat, "00000100145")
        self.assertEqual(employees[1].pis_pasep, "12050901129")

    def test_cin_auto_sync_on_create_and_write(self):
        # 1. Creation with identity_doc_type="cin" automatically syncs
        # l10n_br_rg_code to CPF
        emp = self.env["hr.employee"].create(
            {
                "name": "Employee CIN",
                "vat": "333.222.111-69",
                "identity_doc_type": self.doc_type_cin.id,
                "organ_exp": "SSP",
                "identity_validity": fields.Date.today() + relativedelta(years=10),
            }
        )
        self.assertEqual(emp.identity_doc_type, self.doc_type_cin)
        self.assertEqual(emp.vat, "33322211169")
        self.assertEqual(emp.l10n_br_rg_code, "33322211169")
        self.assertEqual(emp.work_contact_id.l10n_br_rg_code, "33322211169")

        # 2. Writing a new CPF automatically syncs l10n_br_rg_code when CIN
        emp.write({"vat": "444.555.666-19"})
        self.assertEqual(emp.vat, "44455566619")
        self.assertEqual(emp.l10n_br_rg_code, "44455566619")
        self.assertEqual(emp.work_contact_id.l10n_br_rg_code, "44455566619")

    def test_rg_custom_number_not_overwritten(self):
        # Creation with General Registry (RG) allows custom state RG number
        emp = self.env["hr.employee"].create(
            {
                "name": "Employee RG",
                "vat": "777.888.999-41",
                "identity_doc_type": self.doc_type_rg.id,
                "l10n_br_rg_code": "12.345.678-9 SSP/SP",
                "identity_uf_id": self.env.ref("base.state_br_sp").id,
                "organ_exp": "SSP",
            }
        )
        self.assertEqual(emp.identity_doc_type, self.doc_type_rg)
        self.assertEqual(emp.l10n_br_rg_code, "12.345.678-9 SSP/SP")
        self.assertEqual(emp.identity_uf_id.code, "SP")
        self.assertEqual(emp.organ_exp, "SSP")

        # Updating CPF must NOT overwrite custom RG
        emp.write({"vat": "555.666.777-20"})
        self.assertEqual(emp.vat, "55566677720")
        self.assertEqual(emp.l10n_br_rg_code, "12.345.678-9 SSP/SP")

        # Switching to CIN synchronizes with CPF
        emp.write({"identity_doc_type": self.doc_type_cin.id})
        self.assertEqual(emp.identity_doc_type, self.doc_type_cin)
        self.assertEqual(emp.l10n_br_rg_code, "55566677720")

    def test_professional_council_fields(self):
        sp_state = self.env.ref("base.state_br_sp")
        emp = self.env["hr.employee"].create(
            {
                "name": "Engenheiro Silva",
                "vat": "777.888.999-41",
                "professional_council_name": "CREA",
                "professional_council_number": "123456/D",
                "professional_council_state_id": sp_state.id,
                "professional_council_validity": fields.Date.from_string("2030-12-31"),
            }
        )
        self.assertEqual(emp.professional_council_name, "CREA")
        self.assertEqual(emp.professional_council_number, "123456/D")
        self.assertEqual(emp.professional_council_state_id, sp_state)
        self.assertEqual(
            emp.professional_council_validity, fields.Date.from_string("2030-12-31")
        )

    def test_cin_number_follows_cpf_changed_on_contact(self):
        """The CPF changed on the contact (contact form, CRM, portal, import)
        also updates the CIN number shown on the employee."""
        emp = self.env["hr.employee"].create(
            {
                "name": "Employee CIN Contact",
                "vat": "333.222.111-69",
                "identity_doc_type": self.doc_type_cin.id,
            }
        )
        emp.work_contact_id.vat = "44455566619"
        self.assertEqual(emp.vat, "44455566619")
        self.assertEqual(emp.l10n_br_rg_code, "44455566619")

    def test_cin_number_in_employee_form(self):
        hr_officer = new_test_user(
            self.env,
            login="hr_officer_cin",
            groups="base.group_user,hr.group_hr_user",
        )
        emp_form = Form(self.employee.with_user(hr_officer))
        emp_form.vat = "780.048.630-35"
        self.assertEqual(emp_form.l10n_br_rg_code, "78004863035")

    def test_default_identity_doc_type(self):
        # Brazilian nationality in a Brazilian company: CIN
        self.assertEqual(self.employee.identity_doc_type, self.doc_type_cin)
        self.assertEqual(self.employee.l10n_br_rg_code, "85333427135")
        # Foreign nationality: CRNM
        emp_foreign = self.env["hr.employee"].create(
            {"name": "Foreign Default Doc", "country_id": self.env.ref("base.ar").id}
        )
        self.assertEqual(emp_foreign.identity_doc_type, self.doc_type_crnm)
        # A number typed without a type is not replaced by the CPF
        emp_typed = self.env["hr.employee"].create(
            {
                "name": "Typed Number",
                "vat": "777.888.999-41",
                "l10n_br_rg_code": "12.345.678-9",
            }
        )
        self.assertFalse(emp_typed.identity_doc_type)
        self.assertEqual(emp_typed.l10n_br_rg_code, "12.345.678-9")

    def test_foreign_worker_creation(self):
        # 1. Brazilian employee is NOT foreign worker
        self.assertFalse(self.employee.is_foreign_worker)

        # 2. Foreign employee (e.g. Argentina)
        ar_country = self.env.ref("base.ar")
        foreign_emp = self.env["hr.employee"].create(
            {
                "name": "Lionel Foreigner",
                "country_id": ar_country.id,
                "vat": "780.048.630-35",
                "residence_term": "1",
                "entry_condition": "4",
                "permit_no": "V123456-7",
                "visa_no": "987654321",
                "visa_expire": "2028-12-31",
            }
        )
        self.assertTrue(foreign_emp.is_foreign_worker)
        self.assertEqual(foreign_emp.vat, "78004863035")
        self.assertEqual(foreign_emp.permit_no, "V123456-7")
        self.assertEqual(foreign_emp.visa_no, "987654321")
        self.assertEqual(foreign_emp.residence_term, "1")
        self.assertEqual(foreign_emp.entry_condition, "4")

    def test_foreign_worker_vat_validation(self):
        ar_country = self.env.ref("base.ar")
        with self.assertRaises(ValidationError):
            self.env["hr.employee"].create(
                {
                    "name": "Invalid VAT Foreigner",
                    "country_id": ar_country.id,
                    "vat": "123.456.789-00",  # Invalid CPF checksum
                }
            )

    def test_foreign_company_foreign_employee_vat_bypass(self):
        us_country = self.env.ref("base.us")
        foreign_company = self.env["res.company"].create(
            {"name": "US Branch Inc", "country_id": us_country.id}
        )
        partner_us = self.env["res.partner"].create(
            {
                "name": "John Doe US",
                "company_id": foreign_company.id,
                "country_id": us_country.id,
            }
        )
        emp_us = self.env["hr.employee"].create(
            {
                "name": "John Doe US",
                "work_contact_id": partner_us.id,
                "company_id": foreign_company.id,
                "country_id": us_country.id,
                "vat": "987-65-4321",  # US SSN/Tax ID format, not a Brazilian CPF
            }
        )
        self.assertEqual(emp_us.vat, "987-65-4321")
        self.assertFalse(emp_us.is_foreign_worker)
        # No Brazilian identity document defaulted outside a Brazilian company
        self.assertFalse(emp_us.identity_doc_type)

    def test_naturalized_brazilian_employee(self):
        it_country = self.env.ref("base.it")
        br_country = self.env.ref("base.br")
        emp_naturalized = self.env["hr.employee"].create(
            {
                "name": "Giuseppe Naturalizado",
                "country_id": br_country.id,
                "country_of_birth": it_country.id,
                "place_of_birth": "Roma",
                "vat": "780.048.630-35",
                "naturalization_decree": "Portaria nº 456/2021",
                "naturalization_date": "2021-06-15",
                "voter_title": "123456780123",
                "voter_zone": "001",
                "voter_section": "0002",
            }
        )
        self.assertTrue(emp_naturalized.is_naturalized)
        self.assertFalse(emp_naturalized.is_foreign_worker)
        self.assertFalse(emp_naturalized.is_born_in_brazil)
        self.assertEqual(emp_naturalized.vat, "78004863035")
        self.assertEqual(emp_naturalized.place_of_birth, "Roma")
        self.assertEqual(emp_naturalized.naturalization_decree, "Portaria nº 456/2021")
        self.assertEqual(
            emp_naturalized.naturalization_date, fields.Date.to_date("2021-06-15")
        )
        self.assertEqual(emp_naturalized.voter_title, "123456780123")

    def test_native_brazilian_employee(self):
        self.assertFalse(self.employee.is_naturalized)
        self.assertFalse(self.employee.is_foreign_worker)
        self.assertTrue(self.employee.is_born_in_brazil)

        # Test birth city onchange syncs place_of_birth
        sp_city = self.env["res.city"].search([("country_id.code", "=", "BR")], limit=1)
        if sp_city:
            self.employee.birth_city_id = sp_city
            self.employee._onchange_birth_city_id()
            self.assertEqual(self.employee.place_of_birth, sp_city.name)

    def test_foreign_worker_crnm_and_onchange(self):
        ar_country = self.env.ref("base.ar")
        emp_crnm = self.env["hr.employee"].create(
            {
                "name": "Carlos Argentino",
                "country_id": ar_country.id,
                "country_of_birth": ar_country.id,
                "place_of_birth": "Buenos Aires",
                "vat": "780.048.630-35",
                "identity_doc_type": self.doc_type_crnm.id,
                "l10n_br_rg_code": "V987654-Z",
            }
        )
        self.assertTrue(emp_crnm.is_foreign_worker)
        self.assertFalse(emp_crnm.is_naturalized)
        self.assertFalse(emp_crnm.is_born_in_brazil)
        self.assertEqual(emp_crnm.identity_doc_type, self.doc_type_crnm)
        self.assertEqual(emp_crnm.l10n_br_rg_code, "V987654-Z")
        self.assertEqual(emp_crnm.place_of_birth, "Buenos Aires")

    def test_needs_review_reasons(self):
        employee = self.env["hr.employee"].create({"name": "Employee To Review"})
        self.assertFalse(employee.needs_review)

        employee.disability_ids = [(6, 0, [self.disability_multiple_legacy.id])]
        self.assertTrue(employee.needs_review)
        self.assertIn("disability", employee.review_reasons)
        employee.disability_ids = [(5, 0, 0)]
        self.assertFalse(employee.needs_review)

        # seconded worker of the previous version: setting the category confirms
        employee.legacy_seconded_review = True
        self.assertTrue(employee.needs_review)
        employee.worker_category_id = self.env.ref("l10n_br_hr.worker_category_410")
        self.assertFalse(employee.legacy_seconded_review)
        self.assertFalse(employee.needs_review)

        cbo = self.env.ref("l10n_br_hr.cbo_010105")
        employee.job_id = self.env["hr.job"].create(
            {"name": "Job To Review", "cbo_id": cbo.id}
        )
        self.assertFalse(employee.needs_review)
        cbo.active = False
        self.assertTrue(employee.needs_review)
        self.assertIn("CBO", employee.review_reasons)
        cbo.active = True
        self.assertFalse(employee.needs_review)

        relative = self.env["hr.employee.relative"].create(
            {
                "name": "Dependent To Review",
                "employee_id": employee.id,
                "relation_id": self.env.ref("hr_employee_relative.relation_child").id,
                "dependent_type": "03",
            }
        )
        self.assertFalse(employee.needs_review)
        # ended types only exist on dependents registered before the change
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE hr_employee_relative SET dependent_type = '04' WHERE id = %s",
            (relative.id,),
        )
        relative.invalidate_recordset()
        relative.modified(["dependent_type"])
        self.assertTrue(employee.needs_review)

    def test_marital_status_options(self):
        values = dict(self.env["hr.employee"]._get_marital_status_selection())
        self.assertIn("cohabitant", values)
        self.assertIn("separated", values)
        self.assertNotIn("common_law_marriage", values)

    def test_civil_name_on_work_contact(self):
        employee = self.env["hr.employee"].create(
            {"name": "Alex Social Name", "civil_name": "Alexandre Civil Name"}
        )
        self.assertEqual(employee.work_contact_id.legal_name, "Alexandre Civil Name")
        employee.civil_name = "Alexandre Civil"
        self.assertEqual(employee.work_contact_id.legal_name, "Alexandre Civil")
        self.assertEqual(employee.name, "Alex Social Name")

    def test_dependent_irrf_cpf_and_other_description(self):
        rel_child = self.env.ref("hr_employee_relative.relation_child")
        values = {
            "name": "Dependent Rules",
            "employee_id": self.employee.id,
            "relation_id": rel_child.id,
        }
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["hr.employee.relative"].create(
                dict(values, is_irrf_dependent=True)
            )
        with self.assertRaises(ValidationError), self.env.cr.savepoint():
            self.env["hr.employee.relative"].create(dict(values, dependent_type="99"))
        relative = self.env["hr.employee.relative"].create(
            dict(
                values,
                dependent_type="99",
                notes="Nephew under legal custody",
                is_irrf_dependent=True,
                vat="529.982.247-25",
            )
        )
        self.assertEqual(relative.vat, "52998224725")

    def test_worker_category_table_01_codes(self):
        """All codes of eSocial Table 01 (S-1.3), ended ones archived."""
        categories = (
            self.env["hr.worker.category"].with_context(active_test=False).search([])
        )
        expected_codes = {
            *("101", "102", "103", "104", "105", "106", "107", "108", "111"),
            *("201", "202"),
            *(str(code) for code in range(301, 315)),
            *("401", "410", "501"),
            *("701", "711", "712", "721", "722", "723", "731", "734", "738"),
            *("741", "751", "761", "771", "781"),
            *("901", "902", "903", "904", "906"),
        }
        self.assertEqual(set(categories.mapped("code")), expected_codes)
        self.assertEqual(
            set(categories.filtered(lambda c: not c.active).mapped("code")),
            {"107", "108", "308"},
        )

    def test_private_address_brazilian_fields(self):
        state_sp = self.env.ref("base.state_br_sp")
        employee = self.env["hr.employee"].create(
            {
                "name": "Employee Address",
                "private_street": "Rua das Flores, 123 - apto 4",
                "private_city": "sao paulo",
                "private_state_id": state_sp.id,
                "private_country_id": self.env.ref("base.br").id,
            }
        )
        self.assertTrue(employee.private_address_is_br)
        self.assertEqual(employee.private_street_name, "Rua das Flores")
        self.assertEqual(employee.private_street_number, "123")
        self.assertEqual(employee.private_city_id.ibge_code, "3550308")

        # the Brazilian fields write back the native street and city
        employee.private_street_number = "456"
        self.assertEqual(employee.private_street, "Rua das Flores, 456 - apto 4")
        campinas = self.env["res.city"].search([("ibge_code", "=", "3509502")])
        employee.private_city_id = campinas
        self.assertEqual(employee.private_city, "Campinas")
        self.assertEqual(employee.private_state_id, state_sp)

        # the native city changed elsewhere: the city record follows
        employee.write(
            {
                "private_city": "Rio de Janeiro",
                "private_state_id": self.env.ref("base.state_br_rj").id,
            }
        )
        self.assertEqual(employee.private_city_id.ibge_code, "3304557")
        employee.private_city = "Unknown City"
        self.assertFalse(employee.private_city_id)

    def test_document_states_are_brazilian(self):
        """CTPS and CRNM of a foreign worker are also issued in Brazil, so the
        states offered don't follow the nationality."""
        for field_name in ("ctps_uf_id", "identity_uf_id"):
            domain = self.env["hr.employee"]._fields[field_name].domain
            states = self.env["res.country.state"].search(domain)
            self.assertTrue(states)
            self.assertEqual(states.country_id, self.env.ref("base.br"))

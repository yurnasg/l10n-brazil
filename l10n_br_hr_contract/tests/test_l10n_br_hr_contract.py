# Copyright (C) 2016  Daniel Sadamo - KMEE Informática
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo.tests import TransactionCase


class TestL10nBrContract(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.employee = cls.env["hr.employee"].create({"name": "Contract Test Employee"})
        cls.job = cls.env["hr.job"].create({"name": "Contract Test Job"})

    def test_hr_contract_create(self):
        admission = self.env["hr.contract.admission.type"].search([], limit=1)
        labor_bond = self.env["hr.contract.labor.bond.type"].search([], limit=1)
        labor_regime = self.env["hr.contract.labor.regime"].search([], limit=1)
        salary_unit = self.env["hr.contract.salary.unit"].search([], limit=1)
        resignation_cause = self.env["hr.contract.resignation.cause"].search(
            [], limit=1
        )
        notice = self.env["hr.contract.notice.termination"].search([], limit=1)

        contract = self.env["hr.contract"].create(
            {
                "name": "Test Contract",
                "employee_id": self.employee.id,
                "job_id": self.job.id,
                "wage": 2000,
                "notes": "Demo notes",
                "trial_date_end": "2026-03-01",
                "date_start": "2026-03-02",
                "admission_type_id": admission.id if admission else False,
                "labor_bond_type_id": labor_bond.id if labor_bond else False,
                "labor_regime_id": labor_regime.id if labor_regime else False,
                "salary_unit": salary_unit.id if salary_unit else False,
                "welfare_policy": "rgps",
                "discount_union_contribution": True,
                "monthly_hours": 180,
                "weekly_hours": 44,
                "work_schedule_type": "4",
                "resignation_date": "2026-06-20",
                "resignation_cause_id": (
                    resignation_cause.id if resignation_cause else False
                ),
                "notice_of_termination_id": notice.id if notice else False,
                "notice_of_termination_date": "2026-06-20",
            }
        )

        self.assertTrue(contract, "Error on create a l10n_br contract")
        self.assertEqual(contract.welfare_policy, "rgps")
        self.assertEqual(contract.work_schedule_type, "4")

    def test_admission_type(self):
        admission_type = self.env.ref("l10n_br_hr_contract.admission_type_1")
        self.assertEqual(admission_type.code, "1")
        self.assertEqual(admission_type.display_name, "1 - Admission")

        admission_5 = self.env.ref("l10n_br_hr_contract.admission_type_5")
        self.assertEqual(admission_5.code, "5")
        self.assertEqual(admission_5.display_name, "5 - Transfer of domestic employee")

        admission_7 = self.env.ref("l10n_br_hr_contract.admission_type_7")
        self.assertEqual(admission_7.code, "7")

    def test_labor_regime(self):
        labor_regime = self.env.ref("l10n_br_hr_contract.labor_regime_clt")
        self.assertEqual(labor_regime.code, "1")
        self.assertEqual(labor_regime.short_name, "CLT")
        self.assertEqual(labor_regime.display_name, "CLT - Consolidation of Labor Laws")
        self.assertTrue(labor_regime.active)

        # Code 9 (RJU, RJP) must be archived (active=False) per eSocial S-1.3
        rju = self.env.ref("l10n_br_hr_contract.labor_regime_rju")
        self.assertEqual(rju.code, "9")
        self.assertFalse(rju.active)

        rjp = self.env.ref("l10n_br_hr_contract.labor_regime_rjp")
        self.assertEqual(rjp.code, "9")
        self.assertFalse(rjp.active)

    def test_contract_legacy_labor_regime(self):
        rju = self.env.ref("l10n_br_hr_contract.labor_regime_rju")
        clt = self.env.ref("l10n_br_hr_contract.labor_regime_clt")
        contract = self.env["hr.contract"].create(
            {
                "name": "Test Legacy Regime Contract",
                "employee_id": self.employee.id,
                "job_id": self.job.id,
                "wage": 3000,
                "labor_regime_id": rju.id,
            }
        )
        self.assertTrue(contract.has_legacy_labor_regime)
        contract.write({"labor_regime_id": clt.id})
        self.assertFalse(contract.has_legacy_labor_regime)

    def test_labor_bond_type(self):
        bond_10 = self.env.ref("l10n_br_hr_contract.labor_bond_type_10")
        self.assertEqual(bond_10.code, "10")
        self.assertTrue(bond_10.active)

    def test_salary_unit(self):
        unit_7 = self.env.ref("l10n_br_hr_contract.salary_unit_7")
        self.assertEqual(unit_7.code, "7")
        self.assertEqual(unit_7.name, "Not applicable - Variable salary only")

    def test_resignation_cause(self):
        res_01 = self.env.ref("l10n_br_hr_contract.resignation_cause_01")
        self.assertEqual(res_01.code, "01")
        self.assertEqual(res_01.fgts_withdraw_code, "00")
        self.assertEqual(
            res_01.display_name,
            "01 - Dismissal with just cause by the employer",
        )
        self.assertTrue(res_01.active)

        res_02 = self.env.ref("l10n_br_hr_contract.resignation_cause_02")
        self.assertEqual(res_02.code, "02")
        self.assertEqual(res_02.fgts_withdraw_code, "01")

        # Test modern code 33 (Reforma Trabalhista - Art 484-A CLT)
        res_33 = self.env.ref("l10n_br_hr_contract.resignation_cause_33")
        self.assertEqual(res_33.code, "33")
        self.assertEqual(res_33.fgts_withdraw_code, "07")
        self.assertEqual(
            res_33.display_name,
            "33 - Termination by mutual agreement (CLT Art. 484-A)",
        )

        # Test death resignation causes (eSocial Table 19: 10, 48, 49)
        res_10 = self.env.ref("l10n_br_hr_contract.resignation_cause_10")
        self.assertEqual(res_10.code, "10")
        self.assertEqual(res_10.fgts_withdraw_code, "23")

        res_48 = self.env.ref("l10n_br_hr_contract.resignation_cause_48")
        self.assertEqual(res_48.code, "48")
        self.assertEqual(res_48.fgts_withdraw_code, "01")

        res_49 = self.env.ref("l10n_br_hr_contract.resignation_cause_49")
        self.assertEqual(res_49.code, "49")
        self.assertEqual(res_49.fgts_withdraw_code, "01")

        # Codes with an end date in Table 19 are archived
        for code in ("14", "31"):
            cause = self.env.ref(f"l10n_br_hr_contract.resignation_cause_{code}")
            self.assertFalse(cause.active)

    def test_hr_contract_by_death(self):
        res_10 = self.env.ref("l10n_br_hr_contract.resignation_cause_10")
        contract = self.env["hr.contract"].create(
            {
                "name": "Contract Death Test",
                "employee_id": self.employee.id,
                "job_id": self.job.id,
                "wage": 2500,
                "resignation_cause_id": res_10.id,
                "by_death": "Certidão de Óbito nº 123456",
            }
        )
        self.assertEqual(contract.resignation_code, "10")
        self.assertEqual(contract.by_death, "Certidão de Óbito nº 123456")

    def test_hr_contract_job_sync(self):
        new_employee = self.env["hr.employee"].create({"name": "Sync Test Employee"})
        self.assertFalse(new_employee.job_id)

        # 1. Sync on create
        contract = self.env["hr.contract"].create(
            {
                "name": "Contract Sync Test",
                "employee_id": new_employee.id,
                "job_id": self.job.id,
                "wage": 3000,
            }
        )
        self.assertEqual(new_employee.job_id, self.job)

        # 2. Sync on write
        new_job = self.env["hr.job"].create({"name": "Second Test Job"})
        contract.write({"job_id": new_job.id})
        self.assertEqual(new_employee.job_id, new_job)

    def test_notice_termination(self):
        notice_1 = self.env.ref("l10n_br_hr_contract.notice_of_termination_1")
        self.assertEqual(notice_1.code, "1")
        self.assertEqual(notice_1.name, "Worked")
        self.assertEqual(notice_1.display_name, "1 - Worked")
        self.assertTrue(notice_1.active)

        notice_2 = self.env.ref("l10n_br_hr_contract.notice_of_termination_2")
        self.assertEqual(notice_2.code, "2")
        self.assertEqual(notice_2.display_name, "2 - Indemnified")

        notice_3 = self.env.ref("l10n_br_hr_contract.notice_of_termination_3")
        self.assertEqual(notice_3.code, "3")
        self.assertEqual(notice_3.display_name, "3 - Not applicable")

        self.assertFalse(
            self.env.ref(
                "l10n_br_hr_contract.notice_of_termination_4", raise_if_not_found=False
            )
        )

        contract = self.env["hr.contract"].create(
            {
                "name": "Notice Test Contract",
                "employee_id": self.employee.id,
                "job_id": self.job.id,
                "wage": 2000,
                "notice_of_termination_id": notice_1.id,
            }
        )
        self.assertEqual(contract.notice_of_termination_code, "1")

        # Verify search by code and name
        found_name = self.env["hr.contract.notice.termination"].name_search(
            "Indemnified"
        )
        self.assertTrue(any(r[0] == notice_2.id for r in found_name))
        found_code = self.env["hr.contract.notice.termination"].name_search("2")
        self.assertTrue(any(r[0] == notice_2.id for r in found_code))

    def test_contract_department_sync(self):
        dept = self.env["hr.department"].create({"name": "Contract Engineering"})
        emp = self.env["hr.employee"].create({"name": "Dept Sync Test Employee"})
        self.assertFalse(emp.department_id)

        contract = self.env["hr.contract"].create(
            {
                "name": "Contract Dept Sync",
                "employee_id": emp.id,
                "job_id": self.job.id,
                "wage": 3000,
                "department_id": dept.id,
            }
        )
        self.assertTrue(contract)
        self.assertEqual(emp.department_id, dept)

    def test_contract_set_job_in_employee_compat(self):
        new_job = self.env["hr.job"].create({"name": "Compat Job"})
        contract = self.env["hr.contract"].create(
            {
                "name": "Compat Job Contract",
                "employee_id": self.employee.id,
                "job_id": self.job.id,
                "wage": 3500,
            }
        )
        # Directly call legacy compatibility method
        contract.job_id = new_job
        contract.set_job_in_employee()
        self.assertEqual(self.employee.job_id, new_job)

    def test_contract_union_fields(self):
        union = self.env["res.partner"].create(
            {
                "name": "Sindicato dos Metalurgicos",
                "vat": "00000000000191",
                "union_entity_code": "SIND-1234",
                "is_company": True,
            }
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Union Contract",
                "employee_id": self.employee.id,
                "job_id": self.job.id,
                "wage": 4500,
                "partner_union": union.id,
                "discount_union_contribution": True,
            }
        )
        self.assertEqual(contract.partner_union, union)
        self.assertEqual(contract.union_name, "Sindicato dos Metalurgicos")
        self.assertEqual(contract.union_cnpj, "00000000000191")
        self.assertEqual(contract.union_entity_code, "SIND-1234")
        self.assertTrue(contract.discount_union_contribution)

    def test_contract_work_schedule_types(self):
        """Values of eSocial tpRegJor; no default, not to classify contracts."""
        self.assertFalse(
            self.env["hr.contract"]
            .default_get(["work_schedule_type"])
            .get("work_schedule_type")
        )
        for sched in ("1", "2", "3", "4"):
            contract = self.env["hr.contract"].create(
                {
                    "name": f"Schedule Contract {sched}",
                    "employee_id": self.employee.id,
                    "job_id": self.job.id,
                    "wage": 2000,
                    "work_schedule_type": sched,
                }
            )
            self.assertEqual(contract.work_schedule_type, sched)

    def test_contract_data_abstract_models_search(self):
        # 1. Admission type
        found_adm = self.env["hr.contract.admission.type"].name_search("1")
        self.assertTrue(found_adm)
        found_adm_name = self.env["hr.contract.admission.type"].name_search("Admission")
        self.assertTrue(found_adm_name)

        # 2. Labor bond type
        found_bond = self.env["hr.contract.labor.bond.type"].name_search("10")
        self.assertTrue(found_bond)

        # 3. Labor regime
        found_regime = self.env["hr.contract.labor.regime"].name_search("CLT")
        self.assertTrue(found_regime)

        # 4. Resignation cause
        found_res = self.env["hr.contract.resignation.cause"].name_search("01")
        self.assertTrue(found_res)
        found_res_name = self.env["hr.contract.resignation.cause"].name_search(
            "just cause"
        )
        self.assertTrue(found_res_name)

        # 5. Salary unit
        found_unit = self.env["hr.contract.salary.unit"].name_search("7")
        self.assertTrue(found_unit)

    def test_contract_job_sync_keeps_employee_job(self):
        employee = self.env["hr.employee"].create(
            {"name": "Job Kept Employee", "job_id": self.job.id}
        )
        # a contract without a job position doesn't clear the employee job
        self.env["hr.contract"].create(
            {"name": "No Job Contract", "employee_id": employee.id, "wage": 1000}
        )
        self.assertEqual(employee.job_id, self.job)
        # editing a closed contract doesn't change the current job
        old_contract = self.env["hr.contract"].create(
            {
                "name": "Old Contract",
                "employee_id": employee.id,
                "job_id": self.job.id,
                "wage": 1000,
                "state": "close",
            }
        )
        old_contract.job_id = self.env["hr.job"].create({"name": "Old Job"})
        self.assertEqual(employee.job_id, self.job)

    def test_employee_review_includes_contracts(self):
        employee = self.env["hr.employee"].create({"name": "Contract Review Employee"})
        contract = self.env["hr.contract"].create(
            {"name": "Review Contract", "employee_id": employee.id, "wage": 1000}
        )
        self.assertFalse(employee.needs_review)

        contract.legacy_termination_review = True
        self.assertTrue(employee.needs_review)
        self.assertIn("termination data", employee.review_reasons)
        contract.resignation_cause_id = self.env.ref(
            "l10n_br_hr_contract.resignation_cause_02"
        )
        self.assertFalse(contract.legacy_termination_review)
        self.assertFalse(employee.needs_review)

        contract.labor_regime_id = self.env.ref("l10n_br_hr_contract.labor_regime_rju")
        self.assertTrue(employee.needs_review)
        self.assertIn("labor regime", employee.review_reasons)

    def test_contract_legacy_labor_regime_custom_archived(self):
        custom_regime = self.env["hr.contract.labor.regime"].create(
            {"name": "Custom Inactive Regime", "code": "88", "active": False}
        )
        contract = self.env["hr.contract"].create(
            {
                "name": "Custom Inactive Regime Contract",
                "employee_id": self.employee.id,
                "job_id": self.job.id,
                "wage": 3000,
                "labor_regime_id": custom_regime.id,
            }
        )
        self.assertTrue(contract.has_legacy_labor_regime)

        contract.write({"labor_regime_id": False})
        self.assertFalse(contract.has_legacy_labor_regime)

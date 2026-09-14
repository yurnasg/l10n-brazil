# Roadmap & Future Enhancements for `l10n_br_hr`

This document tracks identified architectural improvements, pending refactorings, and future alignments with eSocial and Odoo core.

---

## 1. Worker Categorization & Relationship Types (`employee_type`)

* **Integration with Odoo 18 Core `employee_type`:**
  - The custom `employee_relationship_type` field was removed in favor of Odoo 18's native `employee_type` (`employee`, `student`, `trainee`, `contractor`, `freelance`). Migration `18.0.1.6.0` maps the legacy values (`cedido` becomes `employee`).
* **eSocial Table 01 (Worker Categories):**
  - Model formal worker categories matching eSocial Table 01 codes:
    - `101`: General Employee (CLT)
    - `102`: Apprentice (*Jovem Aprendiz* - Law 10.097/2000)
    - `103`: Intermittent Worker
    - `701`: Individual Contributor / Autonomous (*Autônomo / RPA*)
    - `721` / `722`: Statutory Director (with / without FGTS)
    - `901`: Intern (*Estagiário* - Law 11.788/2008)
* **Action & Menu Separation Cleanup:**
  - Remove the forced `[('employee_relationship_type', '=', 'funcionario')]` domain on the global `hr.open_view_employee_list_my` action to prevent breaking cross-module interoperability (e.g., Projects, Timesheets, Expenses).
  - Replace with non-intrusive Search View filters and group-by options (*Filter by: Regular Employees, Contractors, Interns, Apprentices*).
* **Outsourced Workers & Vendor Linking:**
  - Add `contractor_partner_id` (`Many2one("res.partner")`) on employee records to properly link outsourced workers (*Terceirizados*) to their actual employer/service provider (Law 13.429/2017).

---

## 2. Secondary Document Models & Dead Code Cleanup

* **Carteira de Identidade Nacional (CIN) & Registro Geral (RG) (Lei 14.534/2023 & Decreto 10.977/2022):**
  - Sob a Lei 14.534/2023, a CIN adota o CPF como número único de identificação civil nacional (Art. 13 do Dec. 10.977/2022).
  - Tipo e número do documento ficam no contato (`res.partner`, módulo `l10n_br_base`): `l10n_br_identity_doc_type` (`cin`, `rg`, `crnm`, `other`) e `l10n_br_rg_code`. No colaborador, `identity_doc_type` e `l10n_br_rg_code` são `related` com o contato de trabalho.
  - Quando selecionado `cin`, o número do documento é calculado a partir do CPF (`vat`) no próprio contato. Assim, a alteração do CPF por qualquer caminho (colaborador, contato, CRM, portal, importação) mantém o número atualizado, e o campo fica somente leitura na interface.
  - O tipo padrão segue a nacionalidade (`cin` para brasileiros, `crnm` para estrangeiros) apenas em empresas brasileiras.
  - Convivência com o RG tradicional garantida até 28/02/2032 (Art. 15 do Dec. 10.977/2022), permitindo a digitação livre do número de RG estadual quando `identity_doc_type == 'rg'`.
  - Dados complementares da CIN (Órgão Expedidor, UF, Data de Emissão e Data de Validade) mantidos e explicitados no grupo de Identidade Civil.
* **`hr.identity.type` ([`models/hr_identity_type.py`](file:///c:/Users/yuria/l10n-brazil/l10n_br_hr/models/hr_identity_type.py)):**
  - Converted `employee_ids` to `One2many(inverse_name="identity_type_id")` eliminating the unneeded intermediate Many2many PostgreSQL junction table.
  - Accessible via Configuration menu. Can be linked when detailed professional council identity types (OAB, CRM, CREA) are managed.
* **`hr.civil.certificate.type` ([`models/hr_civil_certificate_type.py`](file:///c:/Users/yuria/l10n-brazil/l10n_br_hr/models/hr_civil_certificate_type.py)):**
  - Review if standard master data for civil certificates (Birth, Marriage, Civil Union, Divorce) should be provided or aligned with CNJ unified matricula standards.
* **Legacy Printed Documents (`ctps`, `creservist`, `voter_title`):**
  - Maintained strictly for historical records without being required or blocking.
  - Digital CTPS is fully unified under CPF (Portaria SEPRT 1.065/2019).
  - Military Reservist and Voter Title documents were removed from mandatory admission events in eSocial (S-2200).
  - Default category (`default="3"`) on `cresv_categ` removed to prevent phantom values on new records.

---

## 3. Brazilian Contract Module Audit (`l10n_br_hr_contract`)

* **Audit Master Data in `l10n_br_hr_contract`:**
  - Standardize XML master data to English source with `.po` translations:
    - `hr_contract_admission_type_data.xml` (Types of Admission / S-2200)
    - `hr_contract_labor_bond_type_data.xml` (Labor Bond Types)
    - `hr_contract_labor_regime_data.xml` (Labor Regimes: CLT, RJP)
    - `hr_contract_resignation_cause_data.xml` (Termination / Resignation Causes / S-2299)
    - `hr_contract_notice_termination_data.xml` (Notice Termination)
    - `hr_contract_salary_unit_data.xml` (Salary Unit)
* **`hr.contract.notice.termination` (`l10n_br_hr_contract/models/hr_contract_notice_termination.py`):**
  - Refactored to inherit `l10n_br_hr.data.abstract`.
  - Codes 1 - Worked, 2 - Indemnified, 3 - Not applicable. eSocial S-2299 has no notice type field: it reports the notice date (`dtAvPrv`) and whether it was indemnified (`indPagtoAPI`).
  - Added related field `notice_of_termination_code` to `hr.contract`.

---

## 4. Gestão do Ciclo de Vida e Arquivamento de Tabelas Oficiais

* **Governança de Versões e Notas Técnicas:**
  - Todas as tabelas oficiais presentes no módulo foram carregadas com base no **eSocial Versão S-1.3 (consolidada até NT 06/2026 rev., 09/04/2026)** e **CBO 2002 MTE**.
  - Ao atualizar o módulo para novas versões do eSocial (ex.: S-1.4) ou incorporar novas Notas Técnicas:
    1. Novos códigos devem ser adicionados aos arquivos XML correspondentes mantendo a convenção de IDs (`<model_name>_<codigo>`).
    2. Códigos extintos ou revogados pela legislação **NUNCA devem ser deletados (`unlink`)** do banco de dados ou removidos dos arquivos XML, para evitar quebra de chave estrangeira com contratos e colaboradores históricos.
    3. Em vez de exclusão, códigos expirados devem ser arquivados adicionando `<field name="active" eval="False" />` no registro XML ou via migração OpenUpgrade (`pre-migrate.py` / `post-migrate.py`).
    4. Nos modelos derivados de `l10n_br_hr.data.abstract`, avaliar em versões futuras a adição explícita dos campos `date_start` e `date_end` (ou `validity_start` / `validity_end`) para permitir filtragem contextual por data de competência da folha de pagamento ou admissão.


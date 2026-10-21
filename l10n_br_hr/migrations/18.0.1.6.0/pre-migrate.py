# Copyright 2026 OCA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE hr_employee
           SET marital = 'cohabitant'
         WHERE marital = 'common_law_marriage'
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE hr_employee
           SET cresv_categ = NULL
         WHERE cresv_categ = '3'
           AND (creservist IS NULL OR btrim(creservist) = '')
        """,
    )
    if openupgrade.column_exists(env.cr, "hr_employee", "cnpj_cpf"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE res_partner rp
               SET vat = regexp_replace(he.cnpj_cpf, '[^0-9A-Za-z]', '', 'g')
              FROM hr_employee he
             WHERE he.work_contact_id = rp.id
               AND he.cnpj_cpf IS NOT NULL
               AND he.cnpj_cpf != ''
               AND (rp.vat IS NULL OR rp.vat = '')
            """,
        )
    if openupgrade.table_exists(env.cr, "hr_employee_hr_identity_type_rel"):
        openupgrade.logged_query(
            env.cr,
            "DROP TABLE hr_employee_hr_identity_type_rel",
        )

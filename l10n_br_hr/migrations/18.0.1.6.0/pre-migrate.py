# Copyright 2026 Escodoo
# Copyright 2026 KMEE, Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    if openupgrade.column_exists(env.cr, "hr_employee", "cnpj_cpf"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE res_partner p
               SET vat = REGEXP_REPLACE(e.cnpj_cpf, '[^0-9]', '', 'g')
              FROM hr_employee e
             WHERE e.work_contact_id = p.id
               AND e.cnpj_cpf IS NOT NULL
               AND e.cnpj_cpf != ''
               AND (p.vat IS NULL OR p.vat = '')
            """,
        )
        openupgrade.drop_columns(env.cr, [("hr_employee", "cnpj_cpf")])

    if openupgrade.column_exists(env.cr, "hr_employee", "employee_relationship_type"):
        openupgrade.logged_query(
            env.cr,
            """
            UPDATE hr_employee
               SET employee_type = CASE
                   WHEN employee_relationship_type = 'autonomo' THEN 'freelance'
                   WHEN employee_relationship_type = 'terceirizado' THEN 'contractor'
                   WHEN employee_relationship_type = 'funcionario' THEN 'employee'
                   WHEN employee_relationship_type = 'cedido' THEN 'employee'
                   ELSE COALESCE(employee_type, 'employee')
               END
             WHERE employee_relationship_type IS NOT NULL
            """,
        )
        # "cedido" didn't tell whether the worker was received or lent: kept
        # for the post-migration, which flags these employees for review
        openupgrade.rename_columns(
            env.cr, {"hr_employee": [("employee_relationship_type", None)]}
        )

    # "common_law_marriage" duplicated the hr "cohabitant" (união estável)
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
        DROP TABLE IF EXISTS hr_employee_hr_identity_type_rel;
        DROP TABLE IF EXISTS hr_identity_type_hr_employee_rel;
        """,
    )

    # hr.deficiency is replaced by hr.disability (post-migration). The ORM
    # drops the columns of removed fields, so keep them under legacy names.
    for column in ("deficiency_id", "deficiency_description"):
        if openupgrade.column_exists(env.cr, "hr_employee", column):
            openupgrade.rename_columns(env.cr, {"hr_employee": [(column, None)]})

    # CBO records were loaded with numeric ids ("1", "2"...): rename them to
    # the ids of the current data file, so the records (and the job positions
    # linked to them) are updated instead of deleted and created again.
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_model_data imd
           SET name = 'cbo_' || cbo.code
          FROM l10n_br_hr_cbo cbo
         WHERE imd.module = 'l10n_br_hr'
           AND imd.model = 'l10n_br_hr.cbo'
           AND imd.res_id = cbo.id
           AND imd.name ~ '^[0-9]+$'
        """,
    )

    # The hr employees action was filtered by employee_relationship_type and
    # a menu was created under the hr namespace: restore the action to its
    # hr definition and remove the menu, which don't belong to this module.
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_act_window action
           SET domain = '[(''company_id'', ''in'', allowed_company_ids)]'
          FROM ir_model_data imd
         WHERE imd.module = 'hr'
           AND imd.name = 'open_view_employee_list_my'
           AND imd.model = 'ir.actions.act_window'
           AND action.id = imd.res_id
           AND action.domain LIKE '%employee_relationship_type%'
        """,
    )
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE ir_act_window action
           SET context = '{''chat_icon'': True}'
          FROM ir_model_data imd
         WHERE imd.module = 'hr'
           AND imd.name = 'open_view_employee_list_my'
           AND imd.model = 'ir.actions.act_window'
           AND action.id = imd.res_id
           AND action.context LIKE '%employee_relationship_type%'
        """,
    )
    openupgrade.delete_records_safely_by_xml_id(
        env, ["hr.menu_open_view_employee_list_my"]
    )

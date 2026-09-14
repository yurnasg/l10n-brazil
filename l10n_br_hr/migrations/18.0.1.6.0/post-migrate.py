# Copyright 2026 KMEE, Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.l10n_br_hr.hooks import post_init_hook
from openupgradelib import openupgrade
from psycopg2 import sql

DISABILITY_BY_DEFICIENCY = {
    "deficiency_1": "l10n_br_hr.disability_physical",
    "deficiency_2": "l10n_br_hr.disability_hearing",
    "deficiency_3": "l10n_br_hr.disability_visual",
    "deficiency_4": "l10n_br_hr.disability_intellectual_mental_legacy",
    "deficiency_5": "l10n_br_hr.disability_multiple_legacy",
    "deficiency_6": "l10n_br_hr.disability_rehabilitated",
}


def _migrate_deficiencies(env):
    """The single deficiency of each employee becomes a disability.
    Deficiencies created by users become archived disabilities, which flag
    the employee for review."""
    deficiency_column = openupgrade.get_legacy_name("deficiency_id")
    description_column = openupgrade.get_legacy_name("deficiency_description")
    if not openupgrade.column_exists(env.cr, "hr_employee", deficiency_column):
        return
    env.cr.execute(
        sql.SQL(
            """
            SELECT deficiency.id, deficiency.name, imd.name,
                   array_agg(employee.id)
              FROM hr_deficiency deficiency
              JOIN hr_employee employee ON employee.{column} = deficiency.id
              LEFT JOIN ir_model_data imd
                ON imd.module = 'l10n_br_hr'
               AND imd.model = 'hr.deficiency'
               AND imd.res_id = deficiency.id
             GROUP BY deficiency.id, deficiency.name, imd.name
            """
        ).format(column=sql.Identifier(deficiency_column))
    )
    employees = env["hr.employee"].with_context(
        active_test=False, tracking_disable=True
    )
    for deficiency_id, name, xmlid, employee_ids in env.cr.fetchall():
        if xmlid in DISABILITY_BY_DEFICIENCY:
            disability = env.ref(DISABILITY_BY_DEFICIENCY[xmlid])
        else:
            disability = env["hr.disability"].create(
                {
                    "name": name,
                    "code": f"deficiency_{deficiency_id}",
                    "active": False,
                }
            )
        employees.browse(employee_ids).write(
            {"disability_ids": [Command.link(disability.id)]}
        )
    openupgrade.logged_query(
        env.cr,
        sql.SQL(
            """
            UPDATE hr_employee
               SET disability_notes = LEFT({column}, 255)
             WHERE {column} IS NOT NULL
               AND {column} != ''
               AND (disability_notes IS NULL OR disability_notes = '')
            """
        ).format(column=sql.Identifier(description_column)),
    )
    openupgrade.drop_columns(
        env.cr,
        [("hr_employee", deficiency_column), ("hr_employee", description_column)],
    )


def _flag_seconded_employees(env):
    """The published "cedido" relationship type didn't tell whether the worker
    was received from or lent to another employer: flag for review."""
    column = openupgrade.get_legacy_name("employee_relationship_type")
    if not openupgrade.column_exists(env.cr, "hr_employee", column):
        return
    env.cr.execute(
        sql.SQL("SELECT id FROM hr_employee WHERE {column} = 'cedido'").format(
            column=sql.Identifier(column)
        )
    )
    employee_ids = [row[0] for row in env.cr.fetchall()]
    env["hr.employee"].with_context(active_test=False, tracking_disable=True).browse(
        employee_ids
    ).write({"legacy_seconded_review": True})
    openupgrade.drop_columns(env.cr, [("hr_employee", column)])


@openupgrade.migrate()
def migrate(env, version):
    _migrate_deficiencies(env)
    _flag_seconded_employees(env)
    # noupdate data isn't applied to the existing relations on update
    openupgrade.load_data(
        env, "l10n_br_hr", "data/hr_employee_relative_relation_data.xml"
    )
    # same default worker category as a new installation
    post_init_hook(env)

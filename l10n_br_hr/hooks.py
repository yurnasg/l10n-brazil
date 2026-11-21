# Copyright (C) 2026 - Present KMEE, Odoo Community Association (OCA)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


def post_init_hook(env):
    """Set the default eSocial worker category of existing employees."""
    employee_types_by_category = {
        "l10n_br_hr.worker_category_101": ("employee", "worker"),
        "l10n_br_hr.worker_category_701": ("freelance",),
    }
    for xmlid, employee_types in employee_types_by_category.items():
        category = env.ref(xmlid, raise_if_not_found=False)
        if category:
            env.cr.execute(
                """
                UPDATE hr_employee
                   SET worker_category_id = %s
                 WHERE worker_category_id IS NULL
                   AND employee_type IN %s
                """,
                (category.id, employee_types),
            )

# Copyright 2026 KMEE, Odoo Community Association (OCA)
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openupgradelib import openupgrade

# Published resignation causes (RAIS codes) mapped by meaning to eSocial
# Table 19. Causes without an equivalent are kept archived on the contracts,
# which are flagged for review.
RESIGNATION_CAUSE_BY_RAIS_CODE = {
    "10": "01",  # justa causa por iniciativa do empregador
    "11": "02",  # sem justa causa por iniciativa do empregador
    "12": "06",  # término do contrato a termo
    "20": "17",  # rescisão indireta
    "21": "07",  # iniciativa do empregado
    "22": "25",  # posse em outro cargo inacumulável (vacância)
    "34": "29",  # redistribuição
    "40": "30",  # mudança de regime trabalhista
    "50": "22",  # reserva remunerada de militar
    "60": "10",  # falecimento
    "62": "10",  # falecimento por acidente do trabalho típico
    "63": "10",  # falecimento por acidente de trajeto
    "64": "10",  # falecimento por doença profissional
    "70": "38",  # aposentadoria por tempo de contribuição, com rescisão
    "72": "38",  # aposentadoria por idade, com rescisão
    "75": "38",  # aposentadoria compulsória
    "79": "38",  # aposentadoria especial, com rescisão
}


def _migrate_resignation_causes(env):
    env.cr.execute(
        """
        SELECT imd.id, cause.id, cause.code
          FROM ir_model_data imd
          JOIN hr_contract_resignation_cause cause ON cause.id = imd.res_id
         WHERE imd.module = 'l10n_br_hr_contract'
           AND imd.model = 'hr.contract.resignation.cause'
           AND imd.name ~ '^hr_contract_resignation_[0-9]+$'
        """
    )
    contracts = env["hr.contract"].with_context(
        active_test=False, tracking_disable=True
    )
    for imd_id, cause_id, code in env.cr.fetchall():
        contract_ids = contracts.search([("resignation_cause_id", "=", cause_id)]).ids
        if not contract_ids:
            continue
        new_code = RESIGNATION_CAUSE_BY_RAIS_CODE.get(code)
        if new_code:
            new_cause = env.ref(f"l10n_br_hr_contract.resignation_cause_{new_code}")
            openupgrade.logged_query(
                env.cr,
                """
                UPDATE hr_contract
                   SET resignation_cause_id = %s
                 WHERE resignation_cause_id = %s
                """,
                (new_cause.id, cause_id),
            )
        else:
            # without its xml id, the published cause isn't deleted by the update
            openupgrade.logged_query(
                env.cr, "DELETE FROM ir_model_data WHERE id = %s", (imd_id,)
            )
            env["hr.contract.resignation.cause"].browse(cause_id).write(
                {"code": f"RAIS {code}", "active": False}
            )
            contracts.browse(contract_ids).write({"legacy_termination_review": True})


def _migrate_notices_of_termination(env):
    # published code 3 "Com justa causa" is now "Not applicable", which is
    # consistent; code 4 "Sem justa causa" isn't a notice type and is removed
    notice = env.ref(
        "l10n_br_hr_contract.notice_of_termination_4", raise_if_not_found=False
    )
    if notice:
        env["hr.contract"].with_context(
            active_test=False, tracking_disable=True
        ).search([("notice_of_termination_id", "=", notice.id)]).write(
            {"notice_of_termination_id": False, "legacy_termination_review": True}
        )
    # the code became required: notice types created by users get one
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE hr_contract_notice_termination
           SET code = 'legacy_' || id
         WHERE code IS NULL
        """,
    )


@openupgrade.migrate()
def migrate(env, version):
    _migrate_resignation_causes(env)
    _migrate_notices_of_termination(env)

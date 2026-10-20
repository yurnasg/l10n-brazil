# Plano — RH brasileiro (`l10n_br_hr` / `l10n_br_hr_contract`): aproveitamento do Odoo, base legal e histórico

## Contexto
A ficha cadastral de RH (sem geração de XML do eSocial) já recebeu CIN, simplificação, correção da
migração publicada→atual e alinhamento de imigrante/dependentes ao eSocial S-1.3. O usuário quer
continuar o backlog aproveitando o Odoo nativo (`C:\Users\yuria\odoo-18`) e os módulos existentes,
com um registro da **base legal** (para validar vigência) e do **que já foi mexido**, para não se perder.

**Decisões já tomadas**
- Migração só da versão publicada (commit `ae5240d731`) para a atual; estados intermediários não.
- Ficha não gera XML. `hr.identity.type` fica como está.
- Nome social: reaproveitar o `legal_name` do contato (`l10n_br_base`) como nome civil.
- "Cedido" publicado é ambíguo → sinal de revisão. Formato: **específico + geral**.
- Endereço: campos brasileiros (cidade é o mais importante), **sincronizados com o endereço nativo**; sem busca de CEP agora.

**Situação (20/10/2026) — Branch rebaseada sobre o upstream 18.0 (d9fcf6b393).**
- **Rebase & Conflitos:** Rebase concluído com sucesso sobre o upstream mais recente; conflitos no party_mixin.py, 
es_partner_view.xml, __manifest__.py e i18n resolvidos; dados de demonstração (demo/) atualizados para os novos modelos.
- **Validação técnica:** 0 erros de sintaxe (python -m compileall limpo em todos os módulos).
- **Alinhamento com Mantenedores:** Guia de perguntas e validação de overengineering consolidado em QUESTIONARIO_DEVS_RH.md.
- **Validação:**
  - 192 testes (base + CRM + RH + contrato, com `pt_BR`), 0 falhas;
  - atualização publicada → atual sem ERROR/WARNING;
  - ruff, pylint-odoo, prettier e `.pot` limpos;
  - 0 textos sem tradução.
- **Registro de cada item:** `JUSTIFICATIVA_l10n_br_base.md`, itens 12 (ficha), 13
  (contrato) e 14 (traduções).
- **Validar:**
  - base legal marcada "conferir" na seção 2;
  - mapeamento das causas RAIS → Tabela 19 (item 13);
  - código de saque FGTS 07 da causa 33.
- **Mudanças em relação ao plano original:**
  - aviso prévio reduzido a 1–3, porque o S-2299 não tem `tpAvisPrev`;
  - admissão 5/6/7 e jornada 1–4 corrigidas pelo leiaute;
  - `civil_name` no lugar de `legal_name`, por conflito com o `hr_contract`.

---

## 1. O que já foi mexido (local, nada commitado — branch `18.0-hr`)
Conferir com `git status` e `git diff --stat HEAD -- <módulo>`. O git não separa autor; a divisão vem do histórico da sessão.

| Módulo | Trabalho seu (antes da sessão) | Nesta sessão |
|---|---|---|
| `l10n_br_base` (+243/−24) | Rótulo "RG / CIN" | 7 bugs (duplicar vários, VAT múltiplo, `fields_to_sync`, outras IEs, busca com máscara, CPF/CNPJ editável — regressão `f501b94146`, visibilidade RG/IE); CIN (`l10n_br_identity_doc_type`, `l10n_br_rg_code` calculado); testes (15 + 42 de caracterização); traduções |
| `l10n_br_crm` (+22) | — | 2 testes |
| `l10n_br_hr` (+8.341/−3.624) | Deficiências, Tabela 01, dependentes (Tabela 07), CBO hierárquico, raça/cor, escolaridade, estrangeiro/naturalizado, `employee_type`, migração 18.0.1.6.0, gancho, menus | CIN `related`; bug UF de expedição; simplificação (§9 da justificativa); migração com `post-migrate.py` novo (§10); imigrante `residence_term`/`entry_condition`, dependente `is_student` + bloqueio 04/07 (§11); traduções; testes (55 com contrato) |
| `l10n_br_hr_contract` (+2.033/−518) | Tabelas do contrato traduzidas, códigos 1–6/Tabela 19, `has_legacy_labor_regime`, `work_schedule_type`, sync de cargo, menus, testes | Nada alterado. **Revisão encontrou problemas de migração** (Fase 3) |
| Fora do git | — | `JUSTIFICATIVA_l10n_br_base.md`, `AVISOS_FORA_DO_RH.md` |

---

## 2. Base legal (para validar)
"Conferir" = citado de memória ou do código; validar número, artigo e vigência.

**Ficha — já implementado**

| Tema | Norma / fonte | Observação |
|---|---|---|
| CIN com número = CPF | Lei 14.534/2023; Decreto 10.977/2022 (art. 13; RG aceito até 28/02/2032, art. 15) | Artigos do ROADMAP — conferir |
| CRNM (ex-RNE) | Lei 13.445/2017; Decreto 9.199/2017 | Conferir |
| Imigrante: prazo de residência / condição de ingresso | Leiaute S-2200 (S-1.3), grupo `trabImig` | Fonte: leiaute |
| Dependente: tipos 04/07 encerrados em 25/04/2023 | Tabela 07 (S-1.3) | Confirmado no arquivo da raiz |
| IRRF: até 21, até 24 se universitário | Lei 9.250/1995, art. 35; RIR/2018 (Decreto 9.580/2018); código cita IN RFB 1.500/2014 | Conferir artigos |
| Salário-família até 14 anos ou inválido | Lei 8.213/1991, arts. 65–66 | Conferir |
| Cota e tipos de deficiência | Lei 8.213/1991 art. 93; Decreto 3.298/1999; Decreto 5.296/2004; Lei 13.146/2015; S-2200 `infoDeficiencia` | Citado no código |
| Categorias de trabalhador | Tabela 01; Portaria Conjunta MTP/RFB nº 33/2022; Leis 6.019/1974, 9.601/1998, 10.097/2000, 11.718/2008, 11.788/2008, 8.069/1990 | Portaria — conferir |
| CBO | Portaria MTE nº 397/2002 | Citado no código |
| CTPS digital | Portaria SEPRT nº 1.065/2019 | Conferir se foi consolidada |
| Raça/cor, escolaridade | S-2200 `racaCor`, `grauInstr` | Fonte: leiaute |

**Ficha — pendente**

| Tema | Norma / fonte | Observação |
|---|---|---|
| CPF do dependente com IRRF | S-2200: `cpfDep` obrigatório se `depIRRF=S` | Conferir IN RFB vigente |
| Descrição do dependente tipo 99 | S-2200: `descrDep` se `tpDep=99` | Fonte: leiaute |
| Tabela 01 completa | Tabela 01 (S-1.3): 304, 307, 308 (encerrado), 309–314, 751 | Confirmado no arquivo da raiz |
| "Cedido" (410) | Tabela 01, código 410 | Ambíguo → revisão |
| Nome social / nome civil | S-2200 `nmTrab` e `nmSoc` (opcional, 70 car.); Decreto 8.727/2016 | Decreto é da adm. pública federal — conferir |
| Endereço residencial | S-2200 grupo `endereco` (`codMunic` IBGE, `bairro`, `nrLograd`; `tpLograd` Tabela 20) | Fonte: leiaute |
| Estado civil | S-2200 `estCiv` (5 opções); união estável: Código Civil art. 1.723 | Conferir |
| RNM × autorização de trabalho | Lei 13.445/2017 (registro e autorização de residência) | Conferir artigos |

**Contrato (`l10n_br_hr_contract`) — citado no código, validar antes da Fase 3**

| Tema | Norma / fonte citada | Dúvidas levantadas |
|---|---|---|
| Motivos de desligamento | Tabela 19 (S-1.3, tabela na raiz, linha 1564); S-2299; Lei 8.036/1990; Circular CAIXA 998/2022 (saque FGTS) | Lista de códigos arquivados no docstring/readme não bate com os dados |
| Tipo de admissão | S-2200 `tpAdmissao` 1–6 | Rótulos de 5 e 6 parecem errados (reintegração é S-2298) |
| Regime trabalhista | S-2200 `tpRegTrab`; Decreto-Lei 5.452/1943 (CLT) | Leiaute atual pode ter só 1 e 2 |
| Aviso prévio | S-2299 `tpAvisPrev` 1–5; CLT art. 487; Lei 12.506/2011 | Conferir se o campo existe no S-1.x |
| Unidade salarial | S-2200 `undSalFixo` 1–7; CLT art. 458 | — |
| Tipo de vínculo | Tabela RAIS/CAGED; Decreto 76.900/1975 | Não é tabela do eSocial |
| Jornada (`work_schedule_type`) | CLT art. 62 | Não segue `tpJornada`; art. 62 alterado pela Lei 14.442/2022 |

---

## 3. Regras de aproveitamento
- **Nunca editar** `odoo-18` nem módulos de outros repositórios OCA (`hr_employee_relative` é do OCA/hr, clonado e ignorado no git). Reaproveitar via `_inherit`, `related`, funções e dados; mudança neles = PR no repositório de origem.
- **Reaproveitar:**
  - `odoo.tools.street_split` (`odoo-18/odoo/tools/misc.py:1949`) — separa "Rua X, 123" em nome/número; junção brasileira "nome, número" como `l10n_br_base/models/res_partner.py:43-55`.
  - `res.city` + `ibge_code` e os dados de cidades do `l10n_br_base`.
  - Estado civil nativo `cohabitant` (já traduzido "União estável" no `hr`).
  - Visto/permissão de trabalho e o cron `hr.ir_cron_data_check_work_permit_validity`.
  - Coluna `notes` do `hr.employee.relative` (descrição do tipo 99).
  - Padrão `related` com `work_contact_id` e o mapeamento de `create` em `l10n_br_hr/models/hr_employee.py` (`contact_fields`).
- **Não usar:** `zip_search()`/assistente do `l10n_br_zip` e `format.address.mixin`/`party.mixin` no funcionário — sobrescrevem `country_id` (nacionalidade). Busca de CEP futura: `l10n_br.zip._consultar_cep()` mapeado para `private_*`.
- **Atenção:** `hr_contract` já define `hr.employee.legal_name` (calculado a partir do nome). O campo novo precisa de outro nome (`civil_name`) para não conflitar.

---

## 4. Fases

### Fase 0 — Registro no repositório
- Criar `PLANO_RH.md` na raiz (fora do git) com as seções 1, 2 e as fases.
- Acrescentar ao `AVISOS_FORA_DO_RH.md`: tradução pt_BR do `employee_type` no `hr` nativo ("Contractor" = "Contratante"; "Employee" e "Worker" = "Funcionário") — reportar ao Odoo.

### Fase 1 — Ficha (`l10n_br_hr`), sem pendências
1. **Sinal de revisão (específico + geral)** — `models/hr_employee.py`, `views/hr_employee_view.xml`, migrações
   - `legacy_seconded_review` (Boolean): marcado pela migração nos antigos "cedido"; limpa sozinho quando `worker_category_id` é gravado; aviso junto à categoria.
   - `needs_review` (gravado, calculado) = `has_legacy_disability` OU `legacy_seconded_review` OU CBO do cargo arquivado (`job_id.cbo_id.active`) OU dependente com tipo 04/07 (`relative_ids.dependent_type`, reaproveitando `ENDED_DEPENDENT_TYPES`).
   - `review_reasons` (texto calculado, não gravado) para um aviso no topo da ficha; coluna "Revisão" e filtro da lista passam a usar `needs_review` (filtro de deficiência continua).
   - Migração: `pre-migrate.py` guarda `employee_relationship_type` com nome legado (em vez de apagar); `post-migrate.py` marca `legacy_seconded_review` onde era `cedido` e apaga a coluna.
   - Atualizar §9 da justificativa (o `needs_review` volta como agregador).
2. **Dependentes** — `models/hr_employee_relative.py`, `views/hr_employee_relative_view.xml`
   - CPF obrigatório quando `is_irrf_dependent` (atributo `required` na lista + constraint).
   - `notes` obrigatório quando `dependent_type == "99"` (atributo na lista + constraint).
   - Ajustar testes que criam dependente de IRRF sem CPF.
3. **Tabela 01 completa** — `data/hr_worker_category_data.xml` (noupdate: registros novos são criados na atualização)
   - Incluir 304, 307, 308 (`active=False`), 309–314, 751 com nomes do arquivo da raiz e `employee_type_default`.
   - Corrigir docstring de `models/hr_worker_category.py` e `readme/DESCRIPTION.md` (dizem que o 308 existe).
4. **Estado civil** — remover `common_law_marriage` e a redeclaração inútil de `marital`; `pre-migrate.py`: `common_law_marriage` → `cohabitant` (valor publicado).
5. **Nome civil** — `civil_name` = `related work_contact_id.legal_name`, editável, na aba de dados pessoais; incluir no `contact_fields` do `create`; ajuda: o nome do funcionário é o nome de uso/social.
6. **RNM × permissão** — sobrescrever só o `help` de `permit_no`.
7. Traduções, testes (sinal de revisão, migração do cedido/estado civil, dependentes, nome civil).

### Fase 2 — Endereço residencial brasileiro sincronizado (`l10n_br_hr`)
- Campos no funcionário:
  - `private_street_name`, `private_street_number`: gravados, calculados de `private_street` com `street_split`; inversa remonta `private_street` como "nome, número".
  - `private_district`: texto (bairro; sem equivalente nativo).
  - `private_city_id` (`res.city`, domínio pela UF): calculado a partir de `private_city` + `private_state_id` (busca por nome normalizado na UF) quando vazio; ao escolher a cidade, grava `private_city`, `private_state_id` e `private_country_id`.
- Complemento continua em `private_street2` e CEP em `private_zip` (nativos).
- Tela: dentro do bloco nativo `o_address_format` da aba "Private Information" (`hr/views/hr_employee_views.xml:139-146`), visível para endereço brasileiro.
- Sem migração: campos novos calculados preenchem a partir dos dados nativos na atualização.

### Fase 3 — `l10n_br_hr_contract` (depois de validar a base legal da seção 2)
- **Migração 18.0.1.3.0** (publicado `18.0.1.2.1`), hoje inexistente:
  - Motivos de desligamento: 27 xmlids antigos (RAIS) removidos → contratos perdem a causa. Mapear por significado (não por código) para a Tabela 19; tabela de mapeamento validada por você.
  - Aviso prévio 3/4 mudam de significado no mesmo xmlid ("Com/Sem justa causa" → "Não aplicável"/"Trabalhado antecipado") → preservar os antigos (arquivados) e marcar contratos para revisão.
  - `code` obrigatório em aviso prévio criado por usuário; `work_schedule_type` = "1" em contratos existentes (decidir vazio × "1"); arquivo de causas `noupdate`.
- **Bug:** `_sync_employee_job` apaga o cargo do funcionário quando o contrato não tem cargo.
- Tela do contrato: remover atributos pré-17 (`modifiers`, `can_create`) e não substituir a div nativa de salário.
- Menus agora visíveis para `hr.group_hr_user` — confirmar intenção.
- `has_legacy_labor_regime` entra no `needs_review` geral (estender o cálculo neste módulo).
- Corrigir dados/documentação após validação (rótulos de admissão 5/6, regime 9, lista de arquivados).
- Os dois módulos precisam sair juntos (o abstrato com `active` só existe no `l10n_br_hr` atual).

### Fase 4 — Fechamento
- Traduções (`.pot` a partir do código, sem dados de CBO; `pt_BR.po` sem tocar obsoletas).
- Justificativa (novos itens), `ROADMAP.md`, `DESCRIPTION.md`.
- pre-commit oficial em máquina com acesso ao GitHub; separar PRs (base → RH+contrato → CRM).

---

## 5. Verificação
- **Testes unitários** por fase (Docker, `MSYS_NO_PATHCONV=1`, tags com barra):
  `docker compose run --rm web odoo -i l10n_br_hr_contract --test-tags=/l10n_br_hr,/l10n_br_hr_contract -d <db> --test-enable --stop-after-init`
  e, no fechamento, base + CRM + RH + contrato juntos; uma rodada com `--load-language=pt_BR`.
- **Teste de atualização publicada→atual** (mesmo método do item 10):
  - `git archive HEAD` de `l10n_br_base`, `l10n_br_hr`, `l10n_br_hr_contract` no `orig_addons` do scratchpad; instalar com dados de demonstração.
  - Preencher via SQL: vínculo `cedido`, estado civil `common_law_marriage`, `private_street` "Rua X, 123" + `private_city` "São Paulo"/SP, contratos com causas de desligamento antigas e aviso prévio 3/4.
  - Copiar o banco; atualizar uma cópia sem e outra com a correção; conferir por SQL (revisão marcada, `cohabitant`, rua/número/cidade preenchidos, causas mapeadas, avisos preservados) e log sem ERROR/WARNING.
- **Lint:** ruff (check + format), pylint-odoo `.pylintrc-mandatory`, prettier (XML, largura 88, indentação 4, sobre cópias LF), `oca-checks-po` no `.pot`.
- Apagar os bancos de teste ao final (manter só `l10n_br_hr_test`).

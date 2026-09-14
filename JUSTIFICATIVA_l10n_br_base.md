# l10n_br_base — Correções de parceiro/empresa e documento de identidade (CIN)

**Versão:** Odoo 18.0 · **Módulos:** `l10n_br_base` (Mature), com ajustes em `l10n_br_hr` e testes em `l10n_br_crm` · **Data:** 2026-09-12

## Resumo

| # | Tipo | Problema | Evidência no código original |
|---|------|----------|------------------------------|
| 1 | Bug | Duplicar vários parceiros de uma vez gera erro | `ValueError: Expected singleton` |
| 2 | Bug | VAT de parceiros estrangeiros perde a pontuação em escrita múltipla | `12-3456789` vira `123456789` |
| 3 | Bug | Alterar um campo comercial da empresa sobrescreve os outros nos contatos | `industry_id` do contato sobrescrito |
| 4 | Bug | A mesma "outra IE" pode ser cadastrada em dois parceiros | Nenhum erro de validação |
| 5 | Bug | Busca rápida (campos many2one) por CNPJ/CPF **com máscara** não encontra o parceiro | `name_search` retorna vazio |
| 6 | Bug | **Não é possível digitar CPF/CNPJ** no formulário de contato ou empresa brasileiros | `can't write on readonly field 'vat_formatted_cnpj'` |
| 7 | Bug | Campos RG e IE aparecem sem rótulo em empresas brasileiras e parceiros estrangeiros | Condições `and` no lugar de `or` na view |
| 8 | Melhoria | Regra "CIN = CPF" aplicada só no funcionário | CPF alterado pelo contato, CRM, portal ou importação deixa a CIN desatualizada |
| 9 | Bug + simplificação | `l10n_br_hr`: UF de expedição filtrada pela nacionalidade; código sem uso ou duplicado na ficha do funcionário | Estrangeiro não consegue informar a UF brasileira da CRNM/CTPS |
| 10 | Bug (atualização) | `l10n_br_hr`: atualizar da versão publicada perdia deficiências, CBO dos cargos e tipos de dependente, e deixava a ação de Funcionários com domínio em campo removido | Banco da 18.0.1.4.0 atualizado: dados vazios, sem nenhum erro no log |
| 11 | Melhoria | `l10n_br_hr`: dados de imigrante e regra de dependente estudante desalinhados do eSocial S-1.3 | Campos do leiaute antigo; IRRF até 24 anos dependia dos tipos 04/07, encerrados em 25/04/2023 |
| 12 | Melhoria | `l10n_br_hr`: ficha sem sinal geral de revisão, regras de dependente do leiaute, Tabela 01 completa, nome civil e endereço brasileiro | CPF de dependente com IRRF e descrição do tipo 99 não exigidos; estado civil "União estável" duplicado; endereço sem município IBGE |
| 13 | Bug + alinhamento | `l10n_br_hr_contract`: atualização da versão publicada apagava causas de desligamento; tabelas citavam campos inexistentes no eSocial | Banco da 18.0.1.2.1 atualizado: contratos sem causa, aviso prévio apagado sem aviso, WARNING de NOT NULL |

Cada bug foi reproduzido por um teste automatizado que falha no código original
(commit `ae5240d731`) e passa após a correção. Além disso, 42 testes de
caracterização comprovam que o comportamento existente não mudou (ver
"Testes de caracterização").

---

## 1. Duplicar vários parceiros de uma vez

**Problema.** Desde o Odoo 17, `copy()` aceita vários registros (ação
*Duplicar* da lista). O override lia `self.is_br_partner` no recordset inteiro.

**Correção.** A regra "não copiar o CPF/CNPJ" saiu de `copy()` e foi para
`copy_data()`, que retorna os valores de cada registro. A decisão passa a ser
tomada por parceiro. Um `default={"vat": ...}` explícito continua sendo
respeitado, e o dicionário `default` de quem chamou não é mais alterado.

**Testes:** `test_copy_multi_br_partners` (falhava → passa), `test_copy_single_br_partner_clears_vat`.

## 2. VAT estrangeiro perde a pontuação em escrita múltipla

**Problema.** `_normalize_vat` usava o país do parceiro com um registro, mas o
país da **empresa ativa** com vários. Numa empresa brasileira, gravar o VAT em
vários parceiros estrangeiros removia a pontuação.

**Correção.** `write()` divide a gravação quando o recordset mistura parceiros
brasileiros e estrangeiros, e `_normalize_vat()` usa o país do primeiro registro
do grupo, que agora é homogêneo. As chamadas usam `super(PartyMixin, grupo)`
para não repetir overrides superiores. Mudança de comportamento: em escrita
múltipla de parceiros **sem país**, o VAT é mantido como digitado, igual ao que já
acontecia com um único parceiro sem país.

**Testes:** `test_write_multi_foreign_partners_keeps_vat_format` (falhava → passa), `test_write_multi_mixed_countries_vat_format`, `test_write_single_foreign_partner_keeps_vat_format`.

## 3. Sincronização comercial ignora `fields_to_sync`

**Problema.** O core passa em `fields_to_sync` só os campos comerciais alterados.
O override (que não propaga o CNPJ para contatos) ignorava o parâmetro e
propagava todos.

**Correção.** Usar `fields_to_sync` quando informado, como no core, mantendo a
exclusão do `vat`.

**Testes:** `test_commercial_sync_only_changed_fields` (falhava → passa).

## 4. "Outras IEs" duplicadas entre parceiros

**Problema.** A validação só comparava com a IE **principal** dos outros
parceiros. A restrição SQL `unique(state_id, partner_id)` só cobre o mesmo
parceiro.

**Correção.** Busca adicional em `state.tax.numbers` pela mesma UF e IE em
outro parceiro. Linhas sem parceiro são ignoradas, e a mensagem de erro é a que
já existia. A regra vale mesmo com `allow_cnpj_multi_ie`, como a validação da IE
principal.

**Testes:** `test_other_ie_duplicated_on_another_partner` (falhava → passa).

## 5. Busca rápida por CNPJ/CPF com máscara

**Problema.** O `name_search` do Odoo 18 filtra por `display_name`. O
`_expand_vat_search_domain` do mixin só expande filtros que começam com `vat`, e
o `display_name` só vira `vat ilike "14.500.536/0001-80"` depois, dentro de
`_search_display_name`. O valor com máscara nunca bate com o VAT gravado sem
pontuação. Os campos many2one de parceiro (pedido, fatura, lead...) usam essa
busca.

**Correção.** Override de `_search_display_name` em `res.partner`, que
acrescenta `cnpj_cpf_stripped <operador> <valor sem pontuação>` para operadores
positivos quando o texto digitado tem pontuação. As buscas sem máscara não mudam.

**Testes:** `test_name_search_masked_cnpj_and_cpf` (CNPJ completo, CNPJ parcial,
CPF, `display_name ilike`). No código original, a mesma verificação falhou no
teste de caracterização.

## 6. CPF/CNPJ não pode ser digitado nos formulários brasileiros

**Problema.** O commit `f501b94146` (02/08/2026) escondeu o `vat` para registros
brasileiros (`invisible="show_l10n_br"`) e passou a mostrar o
`vat_formatted_cnpj`, nos formulários de contato e de empresa. Esse campo é
calculado **sem inversa**, portanto somente leitura: no formulário não há onde
digitar o CPF/CNPJ de um contato ou empresa brasileiros.

**Evidência no original.** Teste de formulário executado sobre o `l10n_br_base`
do commit `ae5240d731`:
`AssertionError: can't write on readonly field 'vat_formatted_cnpj'`, tanto
para `res.partner` quanto para `res.company`.

**Correção** (no `l10n_br_base.party.mixin`, vale para contato e empresa):
- **Inversa `_inverse_vat_formatted_cnpj`:** grava o valor digitado no `vat`, e o
  `write` já guarda o VAT brasileiro sem pontuação. Cobre gravações por código e
  importação.
- **Onchange `_onchange_vat_formatted_cnpj`:** copia o valor para o `vat` na
  própria tela. Sem ele, o formulário enviaria ao salvar o `vat` escondido e
  vazio, e na empresa isso apagava o valor. O onchange só age quando o valor
  digitado difere do formato do `vat` atual, evitando laço.

**Testes:** `test_br_vat_editable_in_partner_form` (inclui a CIN atualizando na
tela), `test_br_vat_editable_in_company_form`.

## 7. Visibilidade dos campos RG e IE

**Problema.** Rótulo e campo usavam condições diferentes, com `and` no lugar de
`or`.

| Campo | Rótulo visível quando | Campo visível quando (antes) | Efeito |
|---|---|---|---|
| RG | BR e pessoa física | `not (is_company and not show_l10n_br)` | Aparecia **sem rótulo** em empresas brasileiras |
| IE | BR e não é contato filho | `not (not is_company and parent_id and not show_l10n_br)` | Aparecia **sem rótulo** em parceiros estrangeiros |

**Correção.**
- **RG (documento de identidade):** visível para qualquer pessoa física,
  inclusive estrangeira, porque a NF-e usa o número como `idEstrangeiro`.
- **IE:** `invisible="not show_l10n_br or (not is_company and parent_id)"`.

## 8. Documento de identidade no contato (CIN = CPF)

**Problema.** O `l10n_br_hr` guardava o tipo de documento no funcionário e o
número (`l10n_br_rg_code`) no contato, e copiava o CPF para a CIN **só no
`hr.employee`**. O CPF do contato também muda pelo formulário do contato, pelo
CRM, pelo portal ou por importação, e nesses casos a CIN ficava desatualizada.

**Contexto (git).** O número já é usado fora do RH: `l10n_br_crm`,
`l10n_br_crm_cnpj_search`, `l10n_br_portal` e `l10n_br_nfe` (`idEstrangeiro`). A
divisão "número no contato, detalhes no funcionário" existe desde a 10.0. Na 8.0
a coluna `inscr_est` guardava IE ou RG; em 2021 (`3bd43fbcb0`) o RG virou campo
próprio; em 2025 foi renomeado para `l10n_br_rg_code` (`ab5908a458`).

**Correção no `l10n_br_base`.**
- Campo `l10n_br_identity_doc_type` (CIN, RG, CRNM/RNE, Outro) no contato, sem
  padrão. O país do contato é o do endereço, não a nacionalidade.
- `l10n_br_rg_code` passa a ser calculado, gravado e editável. A regra fica num
  único método (`_get_l10n_br_identity_number`):
  - **CIN:** o número é o CPF;
  - **outro tipo:** mantém o número digitado;
  - **ao sair da CIN:** apaga o CPF copiado;
  - **sem tipo:** mantém o número.
- O compute sempre atribui valor, porque no Odoo 18 um compute gravado sem
  atribuição grava `False` e apagaria o RG digitado.
- Formulário: `[Tipo] [Número]`, com o número somente leitura na CIN.

**Correção no `l10n_br_hr`.**
- `identity_doc_type` e `l10n_br_rg_code` passam a ser `related` com o contato
  de trabalho. Sai a cópia do CPF em onchange, `create` e `write`.
- O `create` ainda grava CPF, tipo e número no contato, porque o core cria o
  contato depois do `super().create()`. Tipo padrão pela nacionalidade (CIN ou
  CRNM) só em empresa brasileira e só se nenhum número foi informado.
- Onchange só de exibição, usando a mesma regra do contato: no formulário, o
  `related` não recalcula o contato antes de salvar.
- Sai o `force_save` do número, que enviaria valor antigo e sobrescreveria o
  cálculo.
- Órgão emissor, datas, UF e cidade de expedição continuam no funcionário, com
  `groups="hr.group_hr_user"`.

**Compatibilidade.** O `identity_doc_type` nunca foi publicado, então não há
migração. A coluna `l10n_br_rg_code` já existe e não é recalculada na
atualização, então os valores atuais são preservados. Traduções atualizadas em
`l10n_br_base` e `l10n_br_hr`.

**Testes.**
- `l10n_br_base`: `test_cin_number_follows_cpf`,
  `test_rg_number_kept_on_cpf_change`,
  `test_number_without_document_type_kept_on_cpf_change`,
  `test_switch_document_type`, `test_cin_number_in_partner_form`,
  `test_br_vat_editable_in_partner_form`.
- `l10n_br_hr`: `test_cin_number_follows_cpf_changed_on_contact`,
  `test_cin_number_in_employee_form`, `test_default_identity_doc_type`, mais
  os testes de CIN/RG/CRNM que já existiam, sem alteração.
- `l10n_br_crm`: `test_create_contact_keeps_identity_document`,
  `test_lead_from_cin_partner_gets_cpf_as_document`.

## 9. `l10n_br_hr`: UF dos documentos e simplificação da ficha

**Contexto.** O módulo é uma ficha cadastral: não gera XML do eSocial.

**Bug: UF de expedição.** Os campos `identity_uf_id` e `ctps_uf_id` usavam, na
view, o domínio `[('country_id','=',country_id)]`, em que `country_id` é a
**nacionalidade**. Para um estrangeiro, a lista mostrava os estados do país de
origem, mas a CRNM e a CTPS são emitidas no Brasil. **Correção:** domínio
`country_id.code = BR` no próprio campo. **Teste:**
`test_document_states_are_brazilian`.

**Simplificação.** Nada abaixo muda o que o usuário vê na ficha.

| Removido | Por que podia sair |
|---|---|
| `_get_esocial_info_deficiencia` e `_get_esocial_info_estrangeiro` | Montavam dados no formato do XML, sem nenhum chamador. O de estrangeiro usava o leiaute anterior ao S-1.x |
| `needs_review` | Cópia exata de `has_legacy_disability`, com uma coluna gravada e indexada a mais. Filtro e coluna da lista passam a usar `has_legacy_disability` |
| `employee_relationship_type` (compute + inversa) | Duplicava o `employee_type` nativo e não aparecia em nenhuma view. A migração `18.0.1.6.0` já converte os valores e remove a coluna. "Cedido" não tem equivalente e voltava a "funcionário" na próxima mudança de tipo. O `post_init_hook` perde o passo que lia essa coluna e mantém a categoria padrão |
| Cópia do CPF para `identification_id` | Campo nativo oculto (a view o troca por `vat`). A cópia era feita em três lugares e não acompanhava o CPF alterado pelo contato |
| `vat_formatted_cnpj` e `pis_pasep_formatted` do funcionário; `vat_formatted_cnpj`, alias `cpf` e `ESOCIAL_DEPENDENT_TYPES` do dependente | Nenhuma view ou módulo usa. O dependente é modelo novo, sem nada a manter compatível |
| `_onchange_vat`, `onchange_cpf` e `_onchange_pis_pasep` (funcionário e dependente) | Só removiam a pontuação na tela; `create` e `write` já gravam só dígitos |
| Tipo de dependente adivinhado pelo nome do parentesco ("filho", "spouse"...) | Os parentescos padrão já trazem o tipo nos dados do módulo. Nos demais, o tipo é escolhido na linha do dependente |
| `views/hr_menu_views.xml` e `invisible="1"` de campos auxiliares | Arquivo vazio. O Odoo 17+ inclui sozinho os campos usados em `invisible` (`_add_missing_fields`) |

Também:
- a regra "empresa brasileira" repetida em três métodos virou `_is_br_company()`;
- os dois defaults de país viraram um só;
- escolaridade ↔ certificado passou a usar um único dicionário.

**Mantido por compatibilidade.** O `cpf` do funcionário existe no OCA 18.0 e
continua como alias de `vat`, agora com o rótulo "CPF (alias)". Isso elimina o
aviso de log "Two fields (cpf, vat) of hr.employee() have the same label".

**Lint.** Corrigidos os 6 `attribute-string-redundant` e o `missing-return`
apontados pelo `.pylintrc-mandatory`.

**Traduções.**
- **`.pot`:** refeito a partir do código, sem os dados de CBO, como já era. Saem 20
  textos que não existem mais e entram 33, a maioria das telas de CBO, que já
  faltavam.
- **`pt_BR.po`:** mesma sincronização, preservando traduções. As 2.849
  entradas obsoletas (`#~`) não foram tocadas.

**Testes.**
- **Removidos com o código:** `test_hr_disability_esocial_info_helper`,
  `test_employee_type_and_relationship_bridge`,
  `test_employee_relative_name_fallback`.
- **Ajustados:** `test_post_init_hook_worker_category`,
  `test_hr_employee_relative_vat_sanitization`, `test_pis_pasep_sanitization`,
  `test_foreign_worker_creation`.
- **Novo:** `test_document_states_are_brazilian`.

## 10. `l10n_br_hr`: migração da versão publicada

**Regra.** As mudanças deste branch nunca foram publicadas. Por isso a migração
cobre só o salto da versão publicada (18.0.1.4.0, commit `ae5240d731`) para a
atual; estados intermediários do branch não têm migração.

**Método.**
1. Instalação do `l10n_br_hr` publicado (via `git archive`), com dados de
   demonstração.
2. Dados antigos preenchidos: deficiência "Múltipla" com descrição, deficiência
   criada pelo usuário, vínculos "cedido" e "autônomo", `cnpj_cpf` e CBO num
   cargo.
3. Duas cópias do banco atualizadas com o código atual: uma sem e outra com a
   correção da migração.

| Dado | Sem correção | Com correção |
|---|---|---|
| Deficiência e descrição | **Perdidas**: o Odoo remove as colunas dos campos excluídos | Convertidas para deficiências (tabela abaixo); descrição → observações |
| CBO do cargo | **Perdido**: os 2.529 CBOs de id numérico são apagados e recriados | Mantido: ids renomeados para `cbo_<código>`, 3.635 CBOs sem duplicata |
| Ação Funcionários (`hr.open_view_employee_list_my`) | Domínio e contexto no campo removido | Domínio e contexto do `hr` restaurados |
| Menu `hr.menu_open_view_employee_list_my` | Solto na raiz do menu | Removido |
| Tipo de dependente nos parentescos padrão | Vazio: dados `noupdate` não são aplicados na atualização | Preenchido |
| Categoria de trabalhador | Vazia: o `post_init_hook` só roda na instalação | Igual à instalação (101 para funcionários, 701 para autônomos) |
| Tipo de vínculo e `cnpj_cpf` | Já migrados | Sem mudança |

| Deficiência publicada | Deficiência atual |
|---|---|
| Física / Auditiva / Visual / Reabilitado | Física / Auditiva / Visual / Reabilitado |
| Intelectual (Mental) | "Intellectual / Mental" (arquivada, marca revisão) |
| Múltipla | "Multiple" (arquivada, marca revisão) |
| Criada pelo usuário | Nova deficiência arquivada com o mesmo nome (marca revisão) |

**Onde.**
- **`pre-migrate.py`:** colunas de deficiência guardadas com nome legado, ids
  dos CBOs, ação e menu do `hr`.
- **`post-migrate.py`** (novo): deficiências, observações, tipos de dependente e
  categoria padrão.

**Resultado.** Nenhum ERROR, WARNING ou traceback no log. A tabela
`hr_deficiency` continua no banco sem uso, como já acontecia sem a correção.

## 11. `l10n_br_hr`: imigrante e dependentes alinhados ao eSocial S-1.3

**Imigrante (evento S-2200, grupo `trabImig`).**

| Antes | Agora |
|---|---|
| Data de chegada, 12 classificações, "casado(a) com brasileiro(a)" e "filhos brasileiros" (dados do leiaute anterior ao S-1.0) | `residence_term`, tempo de residência (`tmpResid`): prazo indeterminado ou determinado |
| | `entry_condition`, condição de ingresso (`condIng`): refugiado, solicitante de refúgio, reunião familiar, Mercosul, dependente diplomático, Tratado Brasil-Portugal ou outra |

As chaves das opções são os códigos do leiaute. Os campos antigos nunca foram
publicados, então não há migração.

Visto e permissão de trabalho continuam nos campos nativos do Odoo. Eles já
avisam o gestor um mês antes do vencimento da permissão
(`_cron_check_work_permit_validity`), o que atende a residência por prazo
determinado.

**Dependentes (Tabela 07).**
- **Problema.** Os tipos 04 e 07 (filho e irmão/neto universitário) foram
  encerrados em 25/04/2023 e unificados nos tipos 03 e 06. A regra de IRRF até
  24 anos só olhava 04/07, então nunca se aplicava a cadastros novos.
- **Correção:**
  - campo `is_student` (universitário ou escola técnica), exibido para os
    tipos 03 e 06; nesses casos o IRRF vai até 24 anos;
  - salário-família inalterado (até 14 anos);
  - 04 e 07 não podem ser escolhidos em valores novos, e a mensagem indica o tipo
    que os substitui;
  - dependentes que já têm esses códigos continuam editáveis e mantêm a regra de
    24 anos;
  - o tipo padrão do parentesco não oferece mais 04/07.

**Aproveitamento do Odoo.** Não há campo de imigrante nem de dependente para
reaproveitar:
- **`hr`:** só visto e permissão de trabalho, com o aviso de vencimento, e o
  total de filhos (`children`).
- **Localizações nativas:** a brasileira (`l10n_br`, `l10n_br_sales`,
  `l10n_br_website_sale`) não tem nada de RH; a única que estende o funcionário
  é a mexicana (CURP e RFC).
- **`l10n_br` para o endereço:** traz 5.570 cidades com faixas de CEP (sem código
  IBGE), CPF/CNPJ como tipos de identificação e rua/número/complemento no
  parceiro. Isso será útil se o endereço residencial for alinhado.

**Testes.**
- **Novo:** `test_dependent_student_and_ended_types`.
- **Ajustados:** `test_foreign_worker_creation`,
  `test_employee_relative_auto_sync_native_esocial` e
  `test_hr_employee_relative_rules_automation`.

**Fontes.** Tabelas do eSocial S-1.3 (NT 06/2026 rev.), no arquivo da raiz, e
leiaute do S-2200 (grupos `trabImig` e `dependente`).

## 12. `l10n_br_hr`: revisão, dependentes, Tabela 01, nome civil e endereço

**Sinal de revisão (específico + geral).**
- **Específicos, no lugar do dado:**
  - deficiência antiga (`has_legacy_disability`);
  - CBO do cargo arquivado;
  - dependente com tipo 04/07;
  - novo `legacy_seconded_review`: o vínculo "cedido" publicado não dizia se o
    trabalhador foi recebido de outro empregador ou cedido a ele. Quem recebe
    usa a categoria 410 da Tabela 01. O sinal é desmarcado ao escolher a
    categoria.
- **Geral:** `needs_review` (gravado) junta os motivos. `review_reasons` mostra os
  motivos num aviso no topo da ficha, e a lista ganha coluna e filtro. O
  `l10n_br_hr_contract` acrescenta os motivos dos contratos. O `needs_review`
  removido no item 9 era cópia de um único sinal; agora agrega vários.

**Dependentes (leiaute S-2200).**
- CPF obrigatório quando deduz IRRF (`cpfDep` se `depIRRF=S`): atributo na lista e
  validação no modelo.
- Descrição obrigatória para o tipo 99 (`descrDep`), reaproveitando as notas do
  `hr_employee_relative`.

**Tabela 01 completa.** Entram 304, 307, 308 (encerrado em 25/04/2023, arquivado),
309 a 314 e 751, conferidos no arquivo de tabelas S-1.3. O README e o docstring já
citavam o 308.

**Estado civil.** O `hr` nativo já traduz `cohabitant` como "União estável"; a
opção extra `common_law_marriage` duplicava o texto. Ela sai, e a migração
converte o valor publicado.

**Nome civil.** `civil_name` usa o `legal_name` do contato de trabalho
(`l10n_br_base`). O nome do funcionário continua sendo o nome de uso, que pode ser
o social. O campo não se chama `legal_name` porque o `hr_contract` já define esse
nome no funcionário.

**Autorização de trabalho × RNM.** Texto de ajuda: o RNM vai no número do documento
de identidade (CRNM).

**Endereço residencial brasileiro, sincronizado com o nativo.**
- **Logradouro e número** (`private_street_name`, `private_street_number`):
  calculados do `private_street` nativo com `odoo.tools.street_split`. A inversa
  remonta "logradouro, número" no formato do `l10n_br_base`, preservando o
  complemento digitado depois do número.
- **Bairro** (`private_district`): campo novo, sem equivalente nativo.
- **Município** (`private_city_id`, com código IBGE): calculado da cidade e UF
  nativas (nome com ou sem acento). Ao escolher o município, são gravadas cidade,
  UF e país nativos.
- **Na tela:** os campos brasileiros substituem rua e cidade quando o endereço é
  brasileiro. Sem busca de CEP: o `l10n_br_zip` grava `country_id`, que no
  funcionário é a nacionalidade.

**Migração publicada → atual** (acréscimos ao item 10):
- "cedido" → `legacy_seconded_review`;
- `common_law_marriage` → `cohabitant`;
- os campos de endereço são preenchidos a partir dos dados nativos.

**Testes:** `test_needs_review_reasons`, `test_marital_status_options`,
`test_civil_name_on_work_contact`,
`test_dependent_irrf_cpf_and_other_description`,
`test_worker_category_table_01_codes`, `test_private_address_brazilian_fields`.

## 13. `l10n_br_hr_contract`: tabelas do eSocial, bug do cargo e migração

**Correções de base legal**, conferidas no leiaute S-2200/S-2299 (documentação
Senior) e no arquivo de tabelas:

| Item | Antes | Agora |
|---|---|---|
| Tipo de aviso prévio | "S-2299 `tpAvisPrev` 1–5" | O S-2299 não tem esse campo: informa a data do aviso (`dtAvPrv`) e se foi indenizado (`indPagtoAPI`). Fica como classificação do contrato: 1 Trabalhado, 2 Indenizado, 3 Não se aplica (CLT art. 487; Lei 12.506/2011) |
| Tipo de admissão 5 e 6 | "Reintegração", "Reconhecimento judicial" | `tpAdmissao` 5 Transferência do empregado doméstico, 6 Mudança de CPF, e acrescentado o 7 (empresa sucedida inapta) |
| Regime trabalhista | "1, 2, 9 Outros" | `tpRegTrab` só tem 1 (CLT) e 2 (Estatutário). RJU/RJP continuam arquivados e sinalizados |
| Jornada (`work_schedule_type`) | 6 opções, padrão "1" | `tpRegJor` 1–4 (submetido a horário, atividade externa, função especificada, teletrabalho), **sem padrão**: não classifica contratos existentes sozinho |
| Causas 14 e 31 | Ativas | Arquivadas (término em 21/01/2024 e 17/09/2024 na Tabela 19) |
| Código de saque FGTS da causa 33 (art. 484-A) | "01-A" | "07" (Manual SEFIP — **validar**) |

**Bug:** `_sync_employee_job` apagava o cargo do funcionário quando o contrato não
tinha cargo, e editar um contrato encerrado trocava o cargo atual. Agora só copia
o cargo de contratos em rascunho ou em vigor.

**Tela e menus:**
- sem atributos pré-17 (`modifiers`, `can_create`);
- sem substituir a div nativa de salário: a unidade salarial entra no lugar do
  rótulo "/ mês";
- menus de configuração de volta a `hr.group_hr_manager`, como na versão
  publicada;
- aviso de dados de desligamento a revisar.

**Revisão:** `legacy_termination_review` no contrato, desmarcado ao trocar a causa
ou o aviso. O `needs_review` do funcionário soma o regime descontinuado e este
sinal.

**Migração publicada (18.0.1.2.1) → atual** (`migrations/18.0.1.3.0/post-migrate.py`),
com as causas RAIS mapeadas por significado (**validar**):

| Causa publicada (RAIS) | Tabela 19 |
|---|---|
| 10 justa causa do empregador | 01 |
| 11 sem justa causa do empregador | 02 |
| 12 término do contrato | 06 |
| 20 rescisão indireta | 17 |
| 21 iniciativa do empregado | 07 |
| 22 posse em cargo inacumulável | 25 |
| 34 redistribuição | 29 |
| 40 mudança de regime | 30 |
| 50 reserva remunerada | 22 |
| 60, 62, 63, 64 falecimento | 10 |
| 70, 72, 75, 79 aposentadoria com rescisão | 38 |
| 30, 31 transferências; 32 readaptação; 33 cessão; 71, 78, 80 aposentadoria sem rescisão; 73, 74, 76 invalidez | Sem equivalente: a causa fica arquivada ("RAIS NN") e o contrato marcado para revisão |

Também: o aviso publicado 4 ("Sem justa causa") é removido e marca o contrato; o 3
("Com justa causa") vira "Não se aplica"; avisos criados por usuários ganham
código.

**Evidência** (banco da versão publicada com dados antigos; uma cópia sem e outra
com a migração):

| Dado | Sem migração | Com migração |
|---|---|---|
| Contrato com causa 11 | Causa apagada | Causa 02 |
| Contrato com causa 73 | Causa apagada, sem aviso | "RAIS 73" arquivada + revisão |
| Aviso "Sem justa causa" | Apagado, sem aviso | Removido + revisão |
| Aviso criado à mão | Sem código; WARNING `unable to set NOT NULL on column 'code'` | Código `legacy_5`, sem WARNING |
| Funcionários (item 12) | — | Cedido marcado, `cohabitant`, rua/número/IBGE preenchidos, revisão geral com os motivos dos contratos |

**Testes:** `test_contract_job_sync_keeps_employee_job`,
`test_employee_review_includes_contracts`, mais os de admissão, aviso,
causas e jornada ajustados.

## 14. Traduções dos dois módulos

**Processo** (sem editar `.po` à mão):
1. exportar o `.pot` pelo Odoo a partir dos termos em inglês;
2. sincronizar por script: remove textos que não existem mais, atualiza
   referências e preserva traduções e entradas obsoletas;
3. listar por script os textos sem tradução;
4. preencher a partir de um JSON revisado.

O `.pot` do `l10n_br_hr` continua sem os dados de CBO.

---

## Testes de caracterização

**Objetivo.** Provar que o comportamento que **já existia** não mudou.

**Método.**
1. **Cobertura da suíte original:** 95% por linha, mas enganosa. A instalação com
   demonstração executa quase tudo sem verificar resultados. Linhas nunca
   executadas: busca por razão social/CNPJ/IE, inversas de rua da empresa, view
   da empresa, `show_br_vat_format`, IE "ISENTO".
2. **42 testes** em `tests/test_partner_behavior.py`, usando só o que existia no
   original: CPF/CNPJ (criação, escrita, onchange, validação, duplicidade,
   configurações), busca, endereço (formato da rua, bairro, onchanges), sincronia
   empresa→contato, duplicar, IE (inválida, isenta, desligada, outras IEs) e
   empresa (campos no parceiro, CNPJ, onchange de estado, views).
3. **O mesmo arquivo roda nas duas versões:** o `l10n_br_base` do commit
   `ae5240d731` (via `git archive`, primeiro no `--addons-path`) e o modificado.

**Resultado.**

| Versão | Testes | Resultado |
|---|---|---|
| Original | 102 (60 existentes + 42 de caracterização) | 0 falhas |
| Modificada | 117 (os mesmos 102 + 15 das mudanças) | 0 falhas |

Na primeira rodada, a única falha foi idêntica nas duas versões: a busca com
máscara. Isso levou à correção 5.

---

## Validação

Ambiente: Docker (`odoo:18.0`, build 20260908), PostgreSQL 16.

| Suíte | Original | Modificada |
|---|---|---|
| `l10n_br_base` | 102 testes, 0 falhas | 117 testes, 0 falhas |
| `l10n_br_base` + `l10n_br_crm` + `l10n_br_hr` + `l10n_br_hr_contract` (antes do item 11) | — (o RH depende da base nova) | 183 testes, 0 falhas |
| `l10n_br_hr` + `l10n_br_hr_contract`, com `pt_BR` carregado (itens 9 a 11) | — | 55 testes, 0 falhas, sem ERROR/WARNING no log |
| Atualização do `l10n_br_hr` 18.0.1.4.0 com dados antigos (item 10) | Perde deficiências, CBO dos cargos e tipos de dependente; ação de Funcionários quebrada | Tudo convertido, sem ERROR/WARNING no log |
| Atualização conjunta dos publicados `l10n_br_base` 18.0.2.1.1, `l10n_br_hr` 18.0.1.4.0 e `l10n_br_hr_contract` 18.0.1.2.1 com dados antigos (itens 12 e 13) | Contratos perdem a causa; aviso prévio apagado sem sinal; WARNING de NOT NULL | Causas mapeadas ou preservadas com revisão; cedido, estado civil e endereço convertidos; sem ERROR/WARNING |
| `l10n_br_base` + `l10n_br_crm` + `l10n_br_hr` + `l10n_br_hr_contract`, com `pt_BR` carregado (itens 1 a 14) | — | **192 testes, 0 falhas**, sem ERROR/WARNING no log |
| `l10n_br_fiscal` + `l10n_br_nfe` + `l10n_br_portal` + `l10n_br_cnpj_search` + `l10n_br_crm_cnpj_search` | 192 testes, 0 falhas | 192 testes, 0 falhas |
| Formulário (digitar CPF/CNPJ em contato e empresa) | 2 falhas (bug 6 confirmado) | passa |

**Notas de ambiente** (não afetam o código):
- **`uom_alias`:** o `l10n_br_fiscal` depende deste módulo OCA, que não vem na
  imagem. Foi instalado com `odoo-addon-uom_alias` numa pasta montada no
  container.
- **Dependências do NF-e:** `requirements.txt` e `test-requirements.txt`
  instalados na mesma pasta (`PYTHONUSERBASE`). O `erpbrasil.base` precisou ser
  reinstalado ali, porque o namespace `erpbrasil` da pasta escondia o da imagem.
- **pre-commit:** o hook oficial da OCA não rodou, porque o ambiente não acessa o
  github.com, de onde os hooks são baixados. Os mesmos checks foram executados
  por fora:

| Check | Resultado nos arquivos alterados | Observação |
|---|---|---|
| `ruff check` / `ruff format --check` | OK | Avisos restantes já existiam em código não alterado |
| `pylint-odoo` (`.pylintrc-mandatory`) | OK na base, no CRM e no RH | Os apontamentos do RH foram corrigidos no item 9 |
| `oca-checks-odoo-module` | OK nas views alteradas | Apontamentos da base (cabeçalho XML, `priority` sem `eval`) são em arquivos não alterados |
| `oca-checks-po` (`po-pretty-format`) | `.pot` da base, do RH e do contrato: OK (o do RH falhava antes do item 9) | Os `pt_BR.po` da base, do RH e do contrato já falham no commit original; comparação feita com LF, porque a cópia de trabalho usa CRLF (`core.autocrlf=true`) |
| `prettier` (plugin XML, largura 88, indentação 4) | View da base: OK. View do RH: formatada com `--write` (só quebra de atributos) | O `ROADMAP.md` do RH já falha no commit original |

```bash
# Original: l10n_br_base do commit ae5240d731 extraído em orig_addons/
docker compose run --rm -v "<orig_addons>:/mnt/orig-addons" web odoo \
  --addons-path=/mnt/orig-addons,/mnt/extra-addons \
  -i l10n_br_base --test-tags=l10n_br_base -d <db> --test-enable --stop-after-init

# Modificada
docker compose run --rm web odoo -i l10n_br_base,l10n_br_crm,l10n_br_hr \
  --test-tags=l10n_br_base,l10n_br_crm,l10n_br_hr -d <db> --test-enable --stop-after-init
```

---

## Fora do escopo (identificado, não alterado)

- **RG gravado na IE pelo CRM.** `l10n_br_crm/models/crm_lead.py:177` e
  `l10n_br_crm_cnpj_search/models/crm_lead.py:43` gravam `l10n_br_rg_code` em
  `l10n_br_ie_code`. É herança da 8.0 (coluna única `inscr_est`). O teste
  existente `test_create_contact` exige esse comportamento, então a correção
  precisa ajustar o teste.
- **Lead sem tipo de documento.** O `crm.lead` tem o próprio `l10n_br_rg_code`,
  com rótulo "RG", e não tem tipo de documento.
- **Tipo de identidade duplicado no RH.** O `l10n_br_hr` mantém o
  `hr.identity.type` (da 10.0), que tem o mesmo papel do tipo de documento.
- **Busca de CEP no endereço do funcionário.** O `l10n_br_zip` grava
  `country_id`, que no funcionário é a nacionalidade. Seria preciso usar
  `l10n_br.zip._consultar_cep()` mapeando para os campos `private_*`.
- **Tabela de vínculos RAIS** (`hr.contract.labor.bond.type`) mantida como
  histórico, fora do eSocial.
- **Validar:** o mapeamento RAIS → Tabela 19 e o código de saque FGTS 07 do
  item 13.
- **README do módulo de compatibilidade.** O `l10n_br_base_l10n_br_compat` diz
  que "remove" o `l10n_latam_identification_type_id`, mas só desativa a view: o
  campo continua sendo preenchido pelo `l10n_br_website_sale`.

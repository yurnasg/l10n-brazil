# l10n-brazil 18.0: pontos encontrados fora do RH

Encontrados durante as mudanças no `l10n_br_base` e no `l10n_br_hr` (branch
`18.0-hr`, a partir do commit `ae5240d731`). Os detalhes das correções da base
estão em `JUSTIFICATIVA_l10n_br_base.md`.

| # | Módulo | Tipo | Situação |
|---|---|---|---|
| 1 | `l10n_br_base` | **Regressão publicada** | Corrigida no PR da base |
| 2 | `l10n_br_crm`, `l10n_br_crm_cnpj_search` | Bug | Não corrigido: PR próprio |
| 3 | `l10n_br_crm` | Melhoria | Não feito: depende do PR da base |
| 4 | `l10n_br_base_l10n_br_compat` | Documentação | Não corrigido |
| 5 | `l10n_br_crm_cnpj_search` | A confirmar | Não verificado |
| 6 | Quem depende do `l10n_br_base` | Aviso de mudança | Faz parte do PR da base |
| 7 | Ambiente Docker local | Nota | — |
| 8 | `hr` nativo (Odoo) | Tradução pt_BR | Reportar ao Odoo |

---

## 1. CPF/CNPJ não pode ser digitado em contato e empresa brasileiros

**Módulo:** `l10n_br_base`. **Afeta quem usa o 18.0 publicado.**

- **Origem:** commit `f501b94146` (02/08/2026, "show formatted CNPJ for BR,
  plain vat for non-BR"), já no `origin/18.0`.
- **Causa:** para registros brasileiros, o formulário esconde o `vat` e mostra o
  `vat_formatted_cnpj`. Esse campo é calculado **sem inversa**, portanto somente
  leitura.
- **Efeito:** no formulário de contato e no de empresa não há onde digitar o
  CPF/CNPJ.
- **Evidência:** teste de formulário no código publicado:
  `AssertionError: can't write on readonly field 'vat_formatted_cnpj'`, em
  `res.partner` e em `res.company`.
- **Correção (PR da base):** inversa e onchange no `vat_formatted_cnpj`, com
  os testes `test_br_vat_editable_in_partner_form` e
  `test_br_vat_editable_in_company_form`.

## 2. CRM grava o RG no campo de Inscrição Estadual

**Módulos:** `l10n_br_crm` e `l10n_br_crm_cnpj_search`.

- **Onde:** `_prepare_customer_values`, no ramo de pessoa física:
  - `l10n_br_crm/models/crm_lead.py:177`
  - `l10n_br_crm_cnpj_search/models/crm_lead.py:43`

  ```python
  "l10n_br_ie_code": self.l10n_br_rg_code,
  "l10n_br_rg_code": self.l10n_br_rg_code,
  ```
- **Efeito:** o contato pessoa física criado a partir de um lead fica com o RG
  também na IE, campo usado em documentos fiscais.
- **Origem:** herança da 8.0, quando IE e RG dividiam a coluna `inscr_est`.
- **Teste que exige o comportamento:** `l10n_br_crm/tests/test_crm_lead.py:186`
  (`test_create_contact`):
  `assertTrue(self.obj_partner.l10n_br_ie_code, "The field RG was not filled")`.
- **Proposta:** remover a linha da IE nos dois módulos e mudar o teste para
  verificar `l10n_br_rg_code`. A correção é pequena, mas muda comportamento, por
  isso vale um PR próprio.

## 3. Lead sem tipo de documento de identidade

**Módulo:** `l10n_br_crm`. **Depende do PR da base.**

- **Situação:**
  - o `crm.lead` tem só `l10n_br_rg_code`, com rótulo "RG";
  - com o PR da base, o contato ganha `l10n_br_identity_doc_type` (CIN, RG,
    CRNM/RNE, Outro), e na CIN o número passa a ser o CPF.
- **Hoje:** o lead converte o número, e o contato fica sem tipo. O número é
  mantido, como cobre o teste `test_create_contact_keeps_identity_document`.
- **Proposta:** tipo de documento no lead, levado ao contato na conversão e
  preenchido pelo onchange do parceiro. Só vale se o CRM atende pessoa física.

## 4. README do módulo de compatibilidade descreve algo que ele não faz

**Módulo:** `l10n_br_base_l10n_br_compat`.

- **O texto diz:** "A compatibilidade remove o campo
  `l10n_latam_identification_type_id`" (`readme/DESCRIPTION.md:17` e
  `README.rst:83`).
- **O módulo faz:**
  - desativa views: `l10n_latam_base.view_partner_latam_form`, as de
    parceiro e empresa do `l10n_br` e a do `base_vat`;
  - no `post_init_hook`, junta as cidades duplicadas do `l10n_br` com as do
    `l10n_br_base`.
- **O campo continua existindo** (`l10n_latam_base`), e o `l10n_br_website_sale`
  nativo o usa nos formulários de checkout e portal
  (`controllers/main.py`, `controllers/portal.py`).
- **Proposta:** corrigir o texto: "oculta o campo nos formulários de parceiro; o
  campo continua existindo e é usado pelo `l10n_br_website_sale`".

## 5. A confirmar: rua do contato criado pelo `l10n_br_crm_cnpj_search`

- **O que se vê no código:**
  - `l10n_br_crm_cnpj_search/models/crm_lead.py:20` envia
    `"street_name": self.street` ao criar o contato;
  - o `l10n_br_crm` envia `self.street_name`.
- **Possível efeito:** se o `street` do lead tiver rua e número, o `street_name`
  do contato recebe o número. Como o endereço brasileiro remonta a rua como
  "rua, número", o número apareceria duas vezes.
- **Situação:** não reproduzido nem testado; vale confirmar.

## 6. Mudanças do PR da base que outros módulos devem conhecer

- **`l10n_br_rg_code` no contato:**
  - passa a ser calculado, gravado e editável;
  - ganha o tipo `l10n_br_identity_doc_type`;
  - gravar o número continua funcionando;
  - na CIN, o número acompanha o CPF.
  - **Quem usa o campo:** `l10n_br_crm`, `l10n_br_crm_cnpj_search`,
    `l10n_br_portal` e `l10n_br_nfe` (`idEstrangeiro`).
- **"Outras IEs" duplicadas entre parceiros passam a gerar erro.** Bancos que já
  têm a mesma UF + IE em dois parceiros recebem erro na próxima gravação dessas
  linhas.
- **Outros comportamentos novos:**
  - `vat_formatted_cnpj` fica editável (item 1);
  - a busca rápida encontra CNPJ/CPF com máscara;
  - duplicar vários parceiros de uma vez funciona;
  - o VAT estrangeiro mantém a pontuação em gravação múltipla;
  - a sincronia comercial respeita `fields_to_sync`.
- **Validação:** os testes de `l10n_br_fiscal`, `l10n_br_nfe`, `l10n_br_portal`,
  `l10n_br_cnpj_search` e `l10n_br_crm_cnpj_search` dão o mesmo resultado antes
  e depois (192 testes, 0 falhas).

## 7. Notas do ambiente Docker local

- **`uom_alias`:** o `l10n_br_fiscal` depende deste módulo OCA, que não vem na
  imagem do Odoo.
- **`erpbrasil.base`:** instalar as dependências do NF-e numa pasta separada
  (`PYTHONUSERBASE`) esconde o namespace `erpbrasil` da imagem; foi preciso
  reinstalar o `erpbrasil.base` na mesma pasta.
- **pre-commit:** o oficial da OCA baixa os hooks do github.com; sem esse acesso,
  os checks precisam rodar um a um.

## 8. Tradução pt_BR do tipo de funcionário no `hr` nativo

- **Onde:** `odoo/addons/hr/i18n/pt_BR.po`, opções de `employee_type`.
- **O que está errado:**
  - "Contractor" está traduzido como **"Contratante"**, que é quem contrata;
    o sentido é "Prestador de serviço" ou "Terceirizado";
  - "Employee" e "Worker" estão traduzidos igualmente como **"Funcionário"**,
    então aparecem duas opções iguais na tela.
- **Proposta:** reportar na tradução do Odoo. Não dá para corrigir de forma
  limpa num módulo OCA.

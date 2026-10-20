# Guia de Alinhamento com os Mantenedores: Recursos Humanos (`l10n-brazil`)

Este documento foi preparado para orientar a conversa com os desenvolvedores originais e mantenedores da OCA (`l10n-brazil`), esclarecendo as motivações do legado, validando decisões arquiteturais e verificando se houve **overengineering** em algum ponto da modernização.

---

## 📌 Contexto Rápido
* **Branch:** `18.0-hr` (rebaseada sobre a versão mais recente do `upstream/18.0` — commit `d9fcf6b393`).
* **Objetivo Geral:** Adequar a suíte de RH (`l10n_br_hr` e `l10n_br_hr_contract`) aos padrões do **Odoo 18**, da **Lei Federal nº 14.534/2023 (CIN)** e do **eSocial S-1.3 (NT 06/2026 rev.)**, garantindo migração segura da versão publicada (`18.0.1.4.0` / `18.0.1.2.1`) sem perda de dados históricos.

---

## ❓ Bloco 1: Validação de Possível "Overengineering" (Simplificar ou Manter?)

### 1. Base Completa do CBO 2002 (Tabelas de Perfil Ocupacional)
* **O que foi feito:** Foram adicionados arquivos CSV da estrutura do CBO 2002 (Grandes Grupos, Subgrupos, Famílias, Ocupações, Sinônimos e o Perfil Ocupacional com mais de 190.000 linhas).
* **Dúvida de Overengineering:** 
  > *"Carregar 190k linhas de perfil ocupacional no banco de dados do Odoo não é overengineering desnecessário para uma localização padrão? O ideal para a OCA não seria manter apenas a tabela enxuta de ocupações/famílias (`l10n_br_hr.cbo.csv` com ~2.600 códigos), evitando lentidão de boot e inchaço no PostgreSQL?"*

### 2. Sistema Agregador de Revisão Cadastral (`needs_review` e `review_reasons`)
* **O que foi feito:** Para evitar que cadastros antigos ficassem incoerentes após a atualização (ex.: funcionário com vínculo "cedido" ambíguo, contratos com motivos de rescisão da RAIS sem equivalência direta, deficiências arquivadas), criamos um campo computado gravado `needs_review` e um aviso contextual (`review_reasons`) no topo da ficha do funcionário e do contrato.
* **Dúvida de Overengineering:**
  > *"Criar essa camada de auditoria/revisão com avisos em tela na ficha do funcionário é bem-vindo pela comunidade ou vocês consideram excesso de código (overengineering de UI) para um módulo de localização?"*

### 3. Endereço Residencial Brasileiro Sincronizado com o Nativo
* **O que foi feito:** O Odoo 18 armazena o endereço privado apenas em `private_street`, `private_street2`, `private_city`, `private_zip`. Criamos campos estruturados brasileiros (`private_street_name`, `private_street_number`, `private_district` e `private_city_id` apontando para `res.city` com código IBGE), usando o utilitário nativo `odoo.tools.street_split` com inversa bidirecional para manter tudo sincronizado com os campos nativos do Odoo.
* **Dúvida de Overengineering:**
  > *"Essa engenharia reversa/sincronismo bidirecional entre o endereço nativo do Odoo e os campos detalhados brasileiros (rua, número, bairro, código IBGE) é o caminho desejado pela OCA, ou vocês preferem manter o endereço residencial nativo simples sem overrides no `hr.employee`?"*

### 4. Coexistência da Tabela RAIS (`hr.contract.labor.bond.type`) e Tabela 01 do eSocial (`hr.worker.category`)
* **O que foi feito:** Mantivemos os modelos legados da RAIS (códigos 10 a 97) e desenvolvemos um mapeamento semântico detalhado na migração para a Tabela 19 / Tabela 01 do eSocial.
* **Dúvida de Overengineering:**
  > *"Vale a pena manter a tabela legada da RAIS no Odoo 18 e manter esse de-para complexo, ou seria melhor simplificar a arquitetura e descontinuar de vez as tabelas da RAIS, adotando exclusivamente as Tabelas 01 e 19 do eSocial?"*

---

## 🏛️ Bloco 2: Motivações Históricas & Alinhamento de Escopo

### 5. Escopo Oficial: Ficha Cadastral vs. Motor de XML do eSocial
* **O que foi feito:** Removemos métodos mortos que geravam fragmentos XML do eSocial antigo (`_get_esocial_info_deficiencia`, `_get_esocial_info_estrangeiro`). Assumimos que o módulo é estritamente uma **ficha cadastral oficial**.
* **Pergunta aos Devs:**
  > *"Qual era a intenção original desses métodos de XML dentro do `l10n_br_hr`? O posicionamento da OCA para o repositório `l10n-brazil` é que a suíte de RH seja exclusivamente o repositório de dados cadastrais (UI + regras brasileiras), deixando a geração de XML/transmissão para um módulo especialista de folha/eSocial?"*

### 6. Centralização da CIN (Lei 14.534/2023) no `res.partner` (`l10n_br_base`)
* **O que foi feito:** Como a CIN unifica a identidade no CPF, colocamos o tipo (`l10n_br_identity_doc_type`) e número (`l10n_br_rg_code`) no `res.partner` (contato). No colaborador (`hr.employee`), o campo é apenas um `related` transparente com o `work_contact_id`.
* **Pergunta aos Devs:**
  > *"Essa centralização no parceiro (`res.partner`) foi pensada para beneficiar outros fluxos (como CRM, Portal e NF-e para `idEstrangeiro`). Vocês concordam com essa abordagem de arquitetura ou preferem que a regra da CIN fique restrita ao funcionário?"*

### 7. Conflito de Nomes: Nome Civil (`civil_name`) vs `legal_name`
* **O que foi feito:** O módulo `hr_contract` do core/OCA já cria um campo calculado chamado `legal_name` no funcionário. Por isso, nomeamos o campo de nome civil brasileiro como `civil_name` (apontando via `related` para o `legal_name` do parceiro no `l10n_br_base`), reservando o campo nativo `name` para nome social/de uso.
* **Pergunta aos Devs:**
  > *"O nome `civil_name` agrada vocês ou vocês recomendam outra convenção de nomenclatura para evitar conflitos no ecossistema OCA?"*

### 8. Código de Saque do FGTS na Rescisão por Acordo (Art. 484-A da CLT - Causa 33)
* **O que foi feito:** O código publicado continha `"01-A"`. No manual do SEFIP/CAIXA consta código `"07"`.
* **Pergunta aos Devs:**
  > *"Qual é o código oficial homologado que vocês esperam nessa tabela para o Odoo 18?"*

---

## 🚀 Bloco 3: Estratégia de Submissão de Pull Requests

Para facilitar a revisão e evitar PRs gigantescos ("monólitos"), recomendamos a seguinte divisão:

1. **PR 1 — `l10n_br_base` (Prioridade Máxima):**
   * Correção da regressão que impede digitação de CPF/CNPJ no formulário de parceiro/empresa (`vat_formatted_cnpj` com inversa e onchange).
   * Suporte à Carteira de Identidade Nacional (CIN) no parceiro.
   * Busca rápida com máscara (`name_search`) e correções de singleton/gravação múltipla.
2. **PR 2 — `l10n_br_hr` + `l10n_br_hr_contract` (Suíte de RH):**
   * Modernização da ficha para eSocial S-1.3 (imigrantes, dependentes com `is_student`, Tabela 01 completa).
   * Alinhamento contratual (admissão 1-7, jornada 1-4, aviso prévio simplificado, Tabela 19).
   * Scripts de migração seguros (`pre-migrate.py` e `post-migrate.py`).
   * Demonstração e testes unitários 100% atualizados.
3. **PR 3 — `l10n_br_crm` (Ajuste Fino):**
   * Correção do lead que gravava RG no campo de IE de pessoa física.

> **Pergunta final:** *"Vocês concordam com esse fatiamento de PRs para facilitar a revisão da comunidade?"*

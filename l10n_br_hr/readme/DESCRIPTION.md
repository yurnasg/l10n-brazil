Este é o módulo base dos recursos humanos brasileiros e implementa
adaptações nos modelos básicos do cadastro de colaboradores, dependentes e
tabelas normativas oficiais:

- Identificação fiscal via `vat` (CPF), armazenada somente com dígitos;
- CTPS com numeração e série;
- PIS/PASEP sanitizado com dígito verificador;
- Certificado de serviço militar / reservista;
- Título de eleitor e RG;
- Dependentes integrados ao módulo `hr_employee_relative` com tipos eSocial;
- Raça / Etnia conforme autodeclaração censitária IBGE e eSocial;
- Tipos de deficiência física e reabilitação conforme legislação e eSocial;
- Categorias formais de trabalhadores (Tabela 01 do eSocial);
- Estrutura completa da Classificação Brasileira de Ocupações (CBO 2002 MTE);
- Tipo de vínculo pelo campo nativo `employee_type`, com a empresa prestadora de serviço dos terceirizados.

---

## Origem, Versão e Vigência das Tabelas Oficiais (Master Data Provenance)

Para viabilizar a rastreabilidade legal, futuras manutenções e o correto arquivamento (`active = False`)
de registros quando versões e Notas Técnicas dos órgãos oficiais forem atualizadas, a tabela abaixo
especifica a fonte de cada carga de dados mestre incluída neste módulo:

| Modelo Odoo | Arquivo de Dados | Tabela Oficial | Sistema / Órgão | Versão / Revisão | Base Legal / Normativa | Diretrizes de Arquivamento e Vigência |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `hr.worker.category` | `data/hr_worker_category_data.xml` | **Tabela 01: Categorias de Trabalhadores** | eSocial / Governo Federal | Versão S-1.3 (NT 06/2026 rev., 09/04/2026) | Portaria Conjunta MTP/RFB nº 33/2022, Lei 6.019/1974, Lei 9.601/1998, Lei 10.097/2000, Lei 11.718/2008, Lei 11.788/2008 | Códigos com data de término oficial (ex.: 107 e 108 Verde e Amarelo - término 31/12/2022; 308 Conscrito - término 25/04/2023) devem ser arquivados (`active=False`) para preservar integridade histórica de contratos passados sem poluir novos cadastros. |
| `l10n_br_hr.cbo` | `data/l10n_br_hr.cbo.csv` | **Classificação Brasileira de Ocupações (CBO 2002)** | MTE (Ministério do Trabalho e Emprego) | CBO 2002 (Estrutura Completa de 5 níveis: Grandes Grupos, Subgrupos Principais, Subgrupos, Famílias e Ocupações) | Portaria MTE nº 397/2002 e atualizações anuais | Ocupações extintas ou descontinuadas em revisões anuais do MTE devem ser arquivadas (`active=False`), mantendo o histórico de cargos ocupados por colaboradores antigos. |
| `hr.disability` | `data/hr_disability_data.xml` | **Tipos de Deficiência para Fins de Cota e eSocial** | eSocial / MTE | Versão S-1.3 (Evento S-2200: campos `defFisica`, `defVisual`, `defAuditiva`, `defMental`, `defIntelectual`, `reabReadap`) | Lei Federal nº 8.213/1991 (Art. 93 - Lei de Cotas), Dec. nº 3.298/1999 (Arts. 3º e 4º), Dec. nº 5.296/2004 e Lei nº 13.146/2015 | Registros oficiais são protegidos contra exclusão física (`unlink`), sendo arquiváveis via interface ou XML em caso de alteração na legislação de cotas. |
| `hr.ethnicity` | `data/hr_ethnicity_data.xml` | **Classificação de Raça/Cor** | IBGE / eSocial | Versão S-1.3 (Evento S-2200: campo `racaCor`) | Metodologia censitária do IBGE (1 - Branca, 2 - Preta, 3 - Parda, 4 - Amarela, 5 - Indígena, 6 - Não informado) | Tabela estável; atualizações mantêm equivalência com o questionário censitário do IBGE. |
| `hr.employee.relative.relation` | `data/hr_employee_relative_relation_data.xml` | **Tabela 07: Tipos de Dependente** | eSocial / Receita Federal do Brasil | Versão S-1.3 (Tabela 07 / Eventos S-2200 e S-2205) | IN RFB nº 1.500/2014 e Regulamento do Imposto de Renda (RIR/2018 - Decreto nº 9.580/2018) | Códigos 04 e 07 tiveram término oficial em 25/04/2023 no eSocial, sendo unificados nos tipos gerais 03 (Filho/Enteado) e 06 (Irmão/Neto). |

### Links e Documentações Oficiais:
- **eSocial - Tabelas Oficiais Versão S-1.3:** [gov.br/esocial/tabelas](https://www.gov.br/esocial/pt-br/documentacao-tecnica/leiautes-esocial-versao-s-1-3-nt-06-2026-rev-09-04-2026/tabelas.html)
- **CBO 2002 - Ministério do Trabalho e Emprego:** [cbo.mte.gov.br](http://www.mtecbo.gov.br)
- **Tabela de Raça/Cor - IBGE:** [ibge.gov.br](https://www.ibge.gov.br)


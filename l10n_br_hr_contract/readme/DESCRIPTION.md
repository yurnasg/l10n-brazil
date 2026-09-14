Este módulo adapta a gestão de contratos de trabalho (`hr.contract`) aos requisitos da Legislação
Brasileira (CLT), da Caixa Econômica Federal (FGTS) e do eSocial:

- Tipos de Admissão e Transferência (eSocial S-2200);
- Motivos de Desligamento / Rescisão e Códigos de Saque do FGTS (eSocial Tabela 19 e Caixa);
- Tipos de Aviso Prévio (CLT Art. 487);
- Unidades de Salário Fixo (eSocial S-2200);
- Regimes Trabalhistas (CLT, Estatutário e Regimes Próprios);
- Tipos de Vínculos Empregatícios (Histórico RAIS/CAGED);
- Enquadramento sindical e parâmetros salariais.

---

## Origem, Versão e Vigência das Tabelas Oficiais (Master Data Provenance)

Para viabilizar a rastreabilidade legal, conformidade fiscal e o correto arquivamento (`active = False`)
de registros quando versões e Notas Técnicas dos órgãos oficiais forem atualizadas, a tabela abaixo
especifica a fonte de cada carga de dados mestre incluída neste módulo:

| Modelo Odoo | Arquivo de Dados | Tabela Oficial | Sistema / Órgão | Versão / Revisão | Base Legal / Normativa | Diretrizes de Arquivamento e Vigência |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `hr.contract.resignation.cause` | `data/hr_contract_resignation_cause_data.xml` | **Tabela 19: Motivos de Desligamento** + Códigos de Saque FGTS | eSocial / Caixa Econômica Federal / MTE | Versão S-1.3 (NT 06/2026 rev., 09/04/2026) / Evento S-2299 | CLT (Decreto-Lei nº 5.452/1943), Lei nº 8.036/1990 (FGTS) e Circular CAIXA nº 998/2022 | Códigos com término na Tabela 19 ficam arquivados (`active=False`): 14 (encerrado em 21/01/2024) e 31 (encerrado em 17/09/2024). Códigos encerrados antes (15, 18 a 20, 28 e 35) não são carregados. As causas da versão anterior (códigos RAIS) são convertidas por significado na migração 18.0.1.3.0; as sem equivalente ficam arquivadas e marcam o contrato para revisão. |
| `hr.contract.admission.type` | `data/hr_contract_admission_type_data.xml` | **Tipo de Admissão (`tpAdmissao`)** | eSocial / MTE | Versão S-1.3 (Evento S-2200) | Manual de Orientação do eSocial (MOS) e CLT | Códigos 1 a 7 (Admissão, Transferência entre empresas do mesmo grupo, Transferência de consórcio, Sucessão/incorporação/cisão/fusão, Transferência do empregado doméstico, Mudança de CPF, Transferência quando a empresa sucedida é inapta). |
| `hr.contract.notice.termination` | `data/hr_contract_notice_termination_data.xml` | **Tipo de Aviso Prévio** (classificação do contrato) | — | O evento S-2299 não tem campo de tipo de aviso: informa a data do aviso (`dtAvPrv`) e se foi indenizado (`indPagtoAPI`) | Lei Federal nº 12.506/2011 e CLT Art. 487 | Códigos 1 a 3 (Trabalhado, Indenizado, Não aplicável). |
| `hr.contract.salary.unit` | `data/hr_contract_salary_unit_data.xml` | **Unidade de Salário Fixo (`undSalFixo`)** | eSocial / MTE | Versão S-1.3 (Evento S-2200) | CLT Art. 458 e segs. | Códigos 1 a 7 (Por hora, Por dia, Por semana, Por quinzena, Por mês, Por tarefa, Não aplicável). |
| `hr.contract.labor.regime` | `data/hr_contract_labor_regime_data.xml` | **Tipo de Regime Trabalhista (`tpRegTrab`)** | eSocial / MTE | Versão S-1.3 (Evento S-2200) | CLT e Legislação Previdenciária | Códigos 1 (CLT) e 2 (Estatutário/legislações específicas). RJU e RJP (código 9 da tabela anterior) ficam arquivados e marcam o contrato para revisão. |
| `hr.contract.labor.bond.type` | `data/hr_contract_labor_bond_type_data.xml` | **Tabela de Tipos de Vínculo Empregatício** | RAIS / CAGED / MTE | Manual de Orientação da RAIS (Ano-Base 2023/2024) | Portaria MTP / Decreto nº 76.900/1975 | Tabela histórica legada pré-eSocial preservada para contratos antigos e compatibilidade retroativa com relatórios da RAIS/CAGED. |

### Links e Documentações Oficiais:
- **eSocial - Tabelas Oficiais Versão S-1.3:** [gov.br/esocial/tabelas](https://www.gov.br/esocial/pt-br/documentacao-tecnica/leiautes-esocial-versao-s-1-3-nt-06-2026-rev-09-04-2026/tabelas.html)
- **FGTS / Manual de Movimentação da Conta Vinculada:** [caixa.gov.br/fgts](https://www.caixa.gov.br/downloads/fgts-manuais-operacionais/Manual_de_Orientacao_Movimentacao_Conta_Vinculada.pdf)
- **Manual de Orientação da RAIS:** [rais.gov.br](http://www.rais.gov.br)


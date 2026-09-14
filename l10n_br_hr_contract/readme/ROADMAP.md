# Roadmap & Gestão do Ciclo de Vida para `l10n_br_hr_contract`

## 1. Gestão do Ciclo de Vida e Arquivamento de Tabelas Contratuais

* **Alinhamento de Versões do eSocial:**
  - As tabelas de motivos de rescisão (Tabela 19), tipos de admissão (`tpAdmissao`), regime de jornada (`tpRegJor`) e unidades de salário foram alinhadas com o **eSocial Versão S-1.3 (NT 06/2026 rev., 09/04/2026)**. O tipo de aviso prévio é uma classificação do contrato: o S-2299 informa apenas a data do aviso e se foi indenizado.
  - Como a legislação do trabalho e as Notas Técnicas alteram motivos de demissão e regras de saque do FGTS com frequência:
    1. **Nenhum registro histórico deve ser excluído fisicamente (`unlink`)**, pois rescisões processadas no passado em folhas anteriores dependem do código persistido.
    2. Registros descontinuados devem ser arquivados utilizando `<field name="active" eval="False" />` nos arquivos XML ou via script de migração.
    3. Para rescisões e contratos, considerar a implementação futura de domínio contextual baseado na data de término do contrato (`date_end`), impedindo a seleção de causas extintas apenas para novas demissões.

## 2. Transição da Tabela de Vínculos da RAIS

* Avaliar a descontinuação gradual da tabela legada `hr.contract.labor.bond.type` (antigo padrão RAIS/CAGED com códigos 10 a 97) em favor da padronização completa na `hr.worker.category` (Tabela 01 do eSocial), mantendo compatibilidade somente onde ainda for exigido por declarações acessórias residuais.


# Origem e Especificação da Tabela CBO 2002 (l10n_br_hr.cbo.csv)

- **Órgão / Sistema Oficial**: Ministério do Trabalho e Emprego (MTE)
- **Classificação**: Classificação Brasileira de Ocupações - CBO 2002
- **Base Legal**: Portaria MTE nº 397, de 9 de outubro de 2002
- **Site Oficial**: [http://www.mtecbo.gov.br](http://www.mtecbo.gov.br)

## Estrutura Hierárquica dos Dados
A tabela foi carregada com a estrutura completa da CBO em 5 níveis hierárquicos:

1. **Grande Grupo (cbo_gg_*)**: 1 dígito (internal_type='view')
2. **Subgrupo Principal (cbo_sgp_*)**: 2 dígitos (internal_type='view')
3. **Subgrupo (cbo_sg_*)**: 3 dígitos (internal_type='view')
4. **Família (cbo_fam_*)**: 4 dígitos (internal_type='view')
5. **Ocupação / Perfil (cbo_ocp_*)**: 6 dígitos (internal_type='normal') com sinônimos associados.

## Diretrizes para Atualizações Futuras e Arquivamento
- Em novas atualizações anuais publicadas pelo MTE, ocupações descontinuadas ou extintas **não devem ser excluídas** do arquivo CSV nem do banco de dados, para evitar quebra de integridade de colaboradores e cargos históricos.
- Para desativar ocupações extintas, o campo ctive deve ser definido como False.

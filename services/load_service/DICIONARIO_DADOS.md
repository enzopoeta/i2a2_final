# Dicionário de Dados - Sistema de Notas Fiscais

## Tabela: notasfiscais

Armazena os dados principais (cabeçalho) das notas fiscais eletrônicas.

| Campo | Tipo | Tamanho | Descrição |
|-------|------|---------|-----------|
| chave_acesso | VARCHAR | 44 | Chave de acesso única da nota fiscal (PK) |
| modelo | VARCHAR | 100 | Modelo da nota fiscal (ex: "55 - NF-E EMITIDA EM SUBSTITUIÇÃO AO MODELO 1 OU 1A") |
| serie_nf | VARCHAR | 10 | Série da nota fiscal |
| numero_nf | VARCHAR | 20 | Número da nota fiscal |
| natureza_operacao | VARCHAR | 255 | Descrição da natureza da operação |
| data_emissao | DATE | - | Data de emissão da nota fiscal |
| evento_mais_recente | VARCHAR | 255 | Último evento registrado para a nota fiscal |
| data_hora_evento_mais_recente | TIMESTAMP | - | Data e hora do último evento |
| cpf_cnpj_emitente | VARCHAR | 20 | CPF ou CNPJ do emitente |
| razao_social_emitente | VARCHAR | 255 | Razão social do emitente |
| inscricao_estadual_emitente | VARCHAR | 20 | Inscrição estadual do emitente |
| uf_emitente | CHAR | 2 | UF do emitente |
| municipio_emitente | VARCHAR | 100 | Município do emitente |
| cnpj_destinatario | VARCHAR | 20 | CNPJ do destinatário |
| nome_destinatario | VARCHAR | 255 | Nome/razão social do destinatário |
| uf_destinatario | CHAR | 2 | UF do destinatário |
| indicador_ie_destinatario | VARCHAR | 50 | Indicador de inscrição estadual do destinatário |
| destino_operacao | VARCHAR | 100 | Tipo de destino da operação (interna/interestadual) |
| consumidor_final | VARCHAR | 50 | Indicador se é consumidor final |
| presenca_comprador | VARCHAR | 100 | Indicador de presença do comprador na transação |
| valor_nota_fiscal | DECIMAL | 15,2 | Valor total da nota fiscal |
| classificacao | VARCHAR | 50 | Classificação da nota fiscal (nullable) |

## Tabela: itensnotafiscal

Armazena os itens/produtos de cada nota fiscal.

| Campo | Tipo | Tamanho | Descrição |
|-------|------|---------|-----------|
| id_item_nf | SERIAL | - | ID único do item (PK) |
| chave_acesso_nf | VARCHAR | 44 | Chave de acesso da nota fiscal (FK) |
| modelo | VARCHAR | 100 | Modelo da nota fiscal |
| serie_nf | VARCHAR | 10 | Série da nota fiscal |
| numero_nf | VARCHAR | 20 | Número da nota fiscal |
| natureza_operacao | VARCHAR | 255 | Descrição da natureza da operação |
| data_emissao | DATE | - | Data de emissão da nota fiscal |
| cpf_cnpj_emitente | VARCHAR | 20 | CPF ou CNPJ do emitente |
| razao_social_emitente | VARCHAR | 255 | Razão social do emitente |
| inscricao_estadual_emitente | VARCHAR | 20 | Inscrição estadual do emitente |
| uf_emitente | CHAR | 2 | UF do emitente |
| municipio_emitente | VARCHAR | 100 | Município do emitente |
| cnpj_destinatario | VARCHAR | 20 | CNPJ do destinatário |
| nome_destinatario | VARCHAR | 255 | Nome/razão social do destinatário |
| uf_destinatario | CHAR | 2 | UF do destinatário |
| indicador_ie_destinatario | VARCHAR | 50 | Indicador de inscrição estadual do destinatário |
| destino_operacao | VARCHAR | 100 | Tipo de destino da operação |
| consumidor_final | VARCHAR | 50 | Indicador se é consumidor final |
| presenca_comprador | VARCHAR | 100 | Indicador de presença do comprador |
| numero_produto | INT | - | Número sequencial do produto na nota |
| descricao_produto | VARCHAR | 500 | Descrição do produto/serviço |
| codigo_ncm_sh | VARCHAR | 20 | Código NCM/SH do produto |
| ncm_sh_tipo_produto | VARCHAR | 255 | Descrição do tipo de produto conforme NCM/SH |
| cfop | VARCHAR | 10 | Código Fiscal de Operações e Prestações |
| quantidade | DECIMAL | 15,4 | Quantidade do produto |
| unidade | VARCHAR | 20 | Unidade de medida |
| valor_unitario | DECIMAL | 15,4 | Valor unitário do produto |
| valor_total | DECIMAL | 15,2 | Valor total do item (quantidade × valor unitário) |

## Relacionamentos

- `itensnotafiscal.chave_acesso_nf` → `notasfiscais.chave_acesso` (FK)
- `impostos_nota_fiscal.chave_acesso_nf` → `notasfiscais.chave_acesso` (FK)
- `impostos_item.id_item_nf` → `itensnotafiscal.id_item_nf` (FK)
- `impostos_item.chave_acesso_nf` → `notasfiscais.chave_acesso` (FK)
- Uma nota fiscal pode ter múltiplos itens
- Cada nota fiscal tem um registro de impostos totais (relação 1:1)
- Cada item pode ter um registro de impostos (relação 1:1)
- Exclusão em cascata: ao excluir uma nota fiscal, todos os itens e impostos são excluídos

## Tabela: impostos_nota_fiscal

Armazena os totais de impostos e valores da nota fiscal conforme declarado no XML.

| Campo | Tipo | Tamanho | Descrição |
|-------|------|---------|-----------|
| id_impostos_nf | SERIAL | - | ID único do registro (PK) |
| chave_acesso_nf | VARCHAR | 44 | Chave de acesso da nota fiscal (FK, UNIQUE) |
| v_bc_icms | DECIMAL | 15,2 | Base de cálculo do ICMS |
| v_icms | DECIMAL | 15,2 | Valor do ICMS |
| v_icms_deson | DECIMAL | 15,2 | Valor do ICMS desonerado |
| v_fcp_uf_dest | DECIMAL | 15,2 | Valor do FCP UF Destino |
| v_icms_uf_dest | DECIMAL | 15,2 | Valor do ICMS UF Destino (DIFAL) |
| v_icms_uf_remet | DECIMAL | 15,2 | Valor do ICMS UF Remetente (DIFAL) |
| v_bc_st | DECIMAL | 15,2 | Base de cálculo do ICMS ST |
| v_st | DECIMAL | 15,2 | Valor do ICMS ST |
| v_ipi | DECIMAL | 15,2 | Valor do IPI |
| v_ipi_devol | DECIMAL | 15,2 | Valor do IPI devolvido |
| v_pis | DECIMAL | 15,2 | Valor do PIS |
| v_cofins | DECIMAL | 15,2 | Valor do COFINS |
| v_ii | DECIMAL | 15,2 | Valor do Imposto de Importação |
| v_tot_trib | DECIMAL | 15,2 | Valor aproximado total de tributos |
| v_prod | DECIMAL | 15,2 | Valor total dos produtos |
| v_frete | DECIMAL | 15,2 | Valor do frete |
| v_seg | DECIMAL | 15,2 | Valor do seguro |
| v_desc | DECIMAL | 15,2 | Valor do desconto |
| v_outro | DECIMAL | 15,2 | Outras despesas acessórias |
| v_nf | DECIMAL | 15,2 | Valor total da NF-e |

## Tabela: impostos_item

Armazena os impostos detalhados de cada item da nota fiscal conforme declarado no XML.

| Campo | Tipo | Tamanho | Descrição |
|-------|------|---------|-----------|
| id_impostos_item | SERIAL | - | ID único do registro (PK) |
| id_item_nf | INT | - | ID do item da nota fiscal (FK) |
| chave_acesso_nf | VARCHAR | 44 | Chave de acesso da nota fiscal (FK) |
| numero_item | INT | - | Número sequencial do item na nota |
| v_tot_trib | DECIMAL | 15,2 | Valor total aproximado de tributos do item |
| icms_orig | INT | - | Origem da mercadoria (0-Nacional, 1-Estrangeira, etc.) |
| icms_cst | VARCHAR | 3 | CST/CSOSN do ICMS |
| icms_mod_bc | INT | - | Modalidade da base de cálculo do ICMS |
| icms_v_bc | DECIMAL | 15,2 | Base de cálculo do ICMS |
| icms_p_icms | DECIMAL | 5,4 | Alíquota do ICMS (percentual) |
| icms_v_icms | DECIMAL | 15,2 | Valor do ICMS |
| icms_uf_v_bc_uf_dest | DECIMAL | 15,2 | Base de cálculo ICMS UF Destino (DIFAL) |
| icms_uf_v_bc_fcp_uf_dest | DECIMAL | 15,2 | Base de cálculo FCP UF Destino |
| icms_uf_p_fcp_uf_dest | DECIMAL | 5,4 | Percentual FCP UF Destino |
| icms_uf_p_icms_uf_dest | DECIMAL | 5,4 | Percentual ICMS UF Destino |
| icms_uf_p_icms_inter | DECIMAL | 5,4 | Percentual ICMS Interestadual |
| icms_uf_p_icms_inter_part | DECIMAL | 5,4 | Percentual ICMS Interestadual partilha |
| icms_uf_v_fcp_uf_dest | DECIMAL | 15,2 | Valor FCP UF Destino |
| icms_uf_v_icms_uf_dest | DECIMAL | 15,2 | Valor ICMS UF Destino |
| icms_uf_v_icms_uf_remet | DECIMAL | 15,2 | Valor ICMS UF Remetente |
| ipi_c_enq | VARCHAR | 10 | Código de enquadramento do IPI |
| ipi_cst | VARCHAR | 3 | CST do IPI |
| ipi_v_bc | DECIMAL | 15,2 | Base de cálculo do IPI |
| ipi_p_ipi | DECIMAL | 5,4 | Alíquota do IPI (percentual) |
| ipi_v_ipi | DECIMAL | 15,2 | Valor do IPI |
| pis_cst | VARCHAR | 3 | CST do PIS |
| pis_v_bc | DECIMAL | 15,2 | Base de cálculo do PIS |
| pis_p_pis | DECIMAL | 5,4 | Alíquota do PIS (percentual) |
| pis_v_pis | DECIMAL | 15,2 | Valor do PIS |
| cofins_cst | VARCHAR | 3 | CST do COFINS |
| cofins_v_bc | DECIMAL | 15,2 | Base de cálculo do COFINS |
| cofins_p_cofins | DECIMAL | 5,4 | Alíquota do COFINS (percentual) |
| cofins_v_cofins | DECIMAL | 15,2 | Valor do COFINS |

## Observações

- Todos os campos são derivados diretamente dos arquivos XML das NF-e
- A chave de acesso é única e serve como identificador principal
- Valores monetários usam precisão de 2 casas decimais
- Percentuais (alíquotas) usam precisão de 4 casas decimais para maior exatidão
- Quantidades podem ter até 4 casas decimais para maior precisão
- Campos de texto têm tamanhos adequados para comportar os dados reais
- Os dados de impostos são extraídos das tags `<total><ICMSTot>` e `<det><imposto>` do XML
- Suporte para DIFAL (Diferencial de Alíquota) em operações interestaduais
- Campos de impostos podem ser nulos caso não estejam presentes no XML 
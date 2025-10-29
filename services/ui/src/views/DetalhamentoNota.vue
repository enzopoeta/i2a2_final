<template>
  <v-container fluid class="pa-6">
    <!-- Loading -->
    <v-row v-if="loading">
      <v-col cols="12" class="text-center">
        <v-progress-circular
          indeterminate
          color="primary"
          size="64"
        ></v-progress-circular>
        <p class="mt-4">Carregando detalhes da nota fiscal...</p>
      </v-col>
    </v-row>

    <!-- Error -->
    <v-row v-else-if="error">
      <v-col cols="12">
        <v-alert type="error" variant="tonal">
          <v-alert-title>Erro ao carregar nota fiscal</v-alert-title>
          {{ error }}
        </v-alert>
        <v-btn color="primary" @click="$router.push('/minhas-notas')" class="mt-4">
          <v-icon class="mr-2">mdi-arrow-left</v-icon>
          Voltar
        </v-btn>
      </v-col>
    </v-row>

    <!-- Conteúdo -->
    <template v-else-if="nota">
      <!-- Header -->
      <v-row>
        <v-col cols="12">
          <v-btn
            variant="text"
            @click="$router.push('/minhas-notas')"
            class="mb-4"
          >
            <v-icon class="mr-2">mdi-arrow-left</v-icon>
            Voltar
          </v-btn>
          
          <h1 class="text-h4">
            <v-icon class="mr-2">mdi-file-document</v-icon>
            Nota Fiscal {{ nota.numero_nf }}
          </h1>
          <p class="text-subtitle-1 text-medium-emphasis">
            {{ formatDate(nota.data_emissao) }}
          </p>
        </v-col>
      </v-row>

      <!-- Botão de Análise Fiscal -->
      <v-row class="mt-4">
        <v-col cols="12">
          <v-alert 
            v-if="analysisSuccess"
            type="success" 
            variant="tonal" 
            closable
            @click:close="analysisSuccess = false"
            class="mb-4"
          >
            <v-alert-title>Análise Fiscal Iniciada!</v-alert-title>
            A análise fiscal desta nota foi enviada para processamento. 
            Aguarde alguns instantes e recarregue a página para ver os resultados.
          </v-alert>
          
          <v-alert 
            v-if="analysisError"
            type="error" 
            variant="tonal" 
            closable
            @click:close="analysisError = null"
            class="mb-4"
          >
            <v-alert-title>Erro ao Iniciar Análise</v-alert-title>
            {{ analysisError }}
          </v-alert>

          <v-card elevation="3" color="purple-lighten-5" class="border-purple">
            <v-card-text class="d-flex align-center justify-space-between flex-wrap ga-4">
              <div>
                <h3 class="text-h6 mb-1">
                  <v-icon color="purple" size="large" class="mr-2">mdi-calculator-variant</v-icon>
                  Análise Fiscal Automatizada
                </h3>
                <p class="text-body-2 text-medium-emphasis mb-0">
                  Calcule impostos (PIS, COFINS, ICMS) e identifique oportunidades de recuperação de crédito
                </p>
              </div>
              <v-btn
                color="purple"
                size="large"
                :loading="processingAnalysis"
                :disabled="processingAnalysis"
                @click="iniciarAnaliseFiscal"
                class="px-8"
              >
                <v-icon class="mr-2">mdi-play-circle</v-icon>
                {{ processingAnalysis ? 'Processando...' : 'Iniciar Análise' }}
              </v-btn>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Informações Principais -->
      <v-row class="mt-4">
        <v-col cols="12" md="6">
          <v-card elevation="2">
            <v-card-title class="bg-primary text-white">
              <v-icon class="mr-2">mdi-domain</v-icon>
              Emitente
            </v-card-title>
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>Nome</v-list-item-title>
                  <v-list-item-subtitle>{{ nota.emit_xnome || 'N/A' }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>CNPJ</v-list-item-title>
                  <v-list-item-subtitle>{{ formatCNPJ(nota.emit_cnpj) }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="nota.emit_xfant">
                  <v-list-item-title>Nome Fantasia</v-list-item-title>
                  <v-list-item-subtitle>{{ nota.emit_xfant }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="nota.emit_xlgr">
                  <v-list-item-title>Endereço</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ nota.emit_xlgr }}, {{ nota.emit_nro }} - {{ nota.emit_xbairro }}<br>
                    {{ nota.emit_xmun }} - {{ nota.emit_uf }} - CEP: {{ nota.emit_cep }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>

        <v-col cols="12" md="6">
          <v-card elevation="2">
            <v-card-title class="bg-secondary text-white">
              <v-icon class="mr-2">mdi-account</v-icon>
              Destinatário
            </v-card-title>
            <v-card-text>
              <v-list density="compact">
                <v-list-item>
                  <v-list-item-title>Nome</v-list-item-title>
                  <v-list-item-subtitle>{{ nota.dest_xnome || 'N/A' }}</v-list-item-subtitle>
                </v-list-item>
                <v-list-item>
                  <v-list-item-title>{{ nota.dest_cnpj ? 'CNPJ' : 'CPF' }}</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ nota.dest_cnpj ? formatCNPJ(nota.dest_cnpj) : formatCPF(nota.dest_cpf) }}
                  </v-list-item-subtitle>
                </v-list-item>
                <v-list-item v-if="nota.dest_xlgr">
                  <v-list-item-title>Endereço</v-list-item-title>
                  <v-list-item-subtitle>
                    {{ nota.dest_xlgr }}, {{ nota.dest_nro }} - {{ nota.dest_xbairro }}<br>
                    {{ nota.dest_xmun }} - {{ nota.dest_uf }} - CEP: {{ nota.dest_cep }}
                  </v-list-item-subtitle>
                </v-list-item>
              </v-list>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Informações da NF -->
      <v-row class="mt-4">
        <v-col cols="12">
          <v-card elevation="2">
            <v-card-title class="bg-info text-white">
              <v-icon class="mr-2">mdi-information</v-icon>
              Informações da Nota Fiscal
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" sm="6" md="3">
                  <div class="text-caption text-medium-emphasis">Chave de Acesso</div>
                  <div class="text-body-2 font-weight-medium">{{ nota.chave_acesso }}</div>
                </v-col>
                <v-col cols="12" sm="6" md="2">
                  <div class="text-caption text-medium-emphasis">Número NF</div>
                  <div class="text-body-2 font-weight-medium">{{ nota.numero_nf }}</div>
                </v-col>
                <v-col cols="12" sm="6" md="2">
                  <div class="text-caption text-medium-emphasis">Série</div>
                  <div class="text-body-2 font-weight-medium">{{ nota.serie || 'N/A' }}</div>
                </v-col>
                <v-col cols="12" sm="6" md="2">
                  <div class="text-caption text-medium-emphasis">Modelo</div>
                  <div class="text-body-2 font-weight-medium">{{ nota.modelo || 'N/A' }}</div>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <div class="text-caption text-medium-emphasis">Classificação</div>
                  <v-chip 
                    :color="getClassificacaoColor(nota.classificacao)"
                    size="small"
                    class="mt-1"
                  >
                    {{ nota.classificacao || 'N/A' }}
                  </v-chip>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Valores -->
      <v-row class="mt-4">
        <v-col cols="12">
          <v-card elevation="2">
            <v-card-title class="bg-success text-white">
              <v-icon class="mr-2">mdi-currency-usd</v-icon>
              Valores
            </v-card-title>
            <v-card-text>
              <v-row>
                <v-col cols="12" sm="6" md="3">
                  <div class="text-caption text-medium-emphasis">Produtos</div>
                  <div class="text-h6">R$ {{ formatCurrency(nota.icmstot_vprod) }}</div>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <div class="text-caption text-medium-emphasis">Frete</div>
                  <div class="text-h6">R$ {{ formatCurrency(nota.icmstot_vfrete) }}</div>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <div class="text-caption text-medium-emphasis">Desconto</div>
                  <div class="text-h6">R$ {{ formatCurrency(nota.icmstot_vdesc) }}</div>
                </v-col>
                <v-col cols="12" sm="6" md="3">
                  <div class="text-caption text-medium-emphasis">Total</div>
                  <div class="text-h5 text-success font-weight-bold">
                    R$ {{ formatCurrency(nota.valor_total) }}
                  </div>
                </v-col>
              </v-row>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Itens da Nota -->
      <v-row class="mt-4">
        <v-col cols="12">
          <v-card elevation="2">
            <v-card-title class="bg-warning text-white">
              <v-icon class="mr-2">mdi-package-variant</v-icon>
              Itens da Nota Fiscal ({{ itens.length }})
            </v-card-title>
            <v-card-text>
              <v-data-table
                :headers="headers"
                :items="itens"
                :items-per-page="10"
                :loading="loadingItens"
                class="elevation-1"
              >
                <template v-slot:item.xprod="{ item }">
                  <div class="text-wrap" style="max-width: 300px;">
                    {{ item.xprod }}
                  </div>
                </template>
                <template v-slot:item.qcom="{ item }">
                  {{ formatNumber(item.qcom) }}
                </template>
                <template v-slot:item.vuncom="{ item }">
                  R$ {{ formatCurrency(item.vuncom) }}
                </template>
                <template v-slot:item.vprod="{ item }">
                  <span class="font-weight-bold">
                    R$ {{ formatCurrency(item.vprod) }}
                  </span>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Impostos do XML -->
      <v-row class="mt-4" v-if="impostosNota || loadingImpostos">
        <v-col cols="12">
          <v-card elevation="2">
            <v-card-title class="bg-teal text-white">
              <v-icon class="mr-2">mdi-file-document-check</v-icon>
              Impostos Declarados no XML da Nota Fiscal
            </v-card-title>
            <v-card-text>
              <!-- Loading -->
              <div v-if="loadingImpostos" class="text-center py-8">
                <v-progress-circular
                  indeterminate
                  color="primary"
                  size="48"
                ></v-progress-circular>
                <p class="mt-4">Carregando impostos...</p>
              </div>

              <!-- Dados de Impostos -->
              <div v-else-if="impostosNota">
                <!-- Totais -->
                <v-row class="mb-4">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-sigma</v-icon>
                      Totais da Nota
                    </h3>
                  </v-col>
                  <v-col cols="6" sm="4" md="3">
                    <v-card variant="tonal" color="blue-lighten-5">
                      <v-card-text>
                        <div class="text-caption text-medium-emphasis">Valor Produtos</div>
                        <div class="text-h6 font-weight-bold text-blue">R$ {{ formatCurrency(impostosNota.v_prod) }}</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                  <v-col cols="6" sm="4" md="3">
                    <v-card variant="tonal" color="green-lighten-5">
                      <v-card-text>
                        <div class="text-caption text-medium-emphasis">Valor Total NF</div>
                        <div class="text-h6 font-weight-bold text-green">R$ {{ formatCurrency(impostosNota.v_nf) }}</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                  <v-col cols="6" sm="4" md="3">
                    <v-card variant="tonal" color="orange-lighten-5">
                      <v-card-text>
                        <div class="text-caption text-medium-emphasis">Total Tributos</div>
                        <div class="text-h6 font-weight-bold text-orange">R$ {{ formatCurrency(impostosNota.v_tot_trib) }}</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                  <v-col cols="6" sm="4" md="3">
                    <v-card variant="tonal" color="red-lighten-5">
                      <v-card-text>
                        <div class="text-caption text-medium-emphasis">Desconto</div>
                        <div class="text-h6 font-weight-bold text-red">R$ {{ formatCurrency(impostosNota.v_desc) }}</div>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>

                <!-- ICMS -->
                <v-row class="mb-4">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-bank</v-icon>
                      ICMS
                    </h3>
                  </v-col>
                  <v-col cols="6" sm="4" md="3">
                    <div class="text-caption text-medium-emphasis">Base de Cálculo</div>
                    <div class="text-body-1 font-weight-medium">R$ {{ formatCurrency(impostosNota.v_bc_icms) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="3">
                    <div class="text-caption text-medium-emphasis">Valor ICMS</div>
                    <div class="text-body-1 font-weight-bold text-primary">R$ {{ formatCurrency(impostosNota.v_icms) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="3" v-if="impostosNota.v_icms_uf_dest">
                    <div class="text-caption text-medium-emphasis">ICMS UF Destino</div>
                    <div class="text-body-1 font-weight-bold text-info">R$ {{ formatCurrency(impostosNota.v_icms_uf_dest) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="3" v-if="impostosNota.v_bc_st">
                    <div class="text-caption text-medium-emphasis">Base ICMS ST</div>
                    <div class="text-body-1">R$ {{ formatCurrency(impostosNota.v_bc_st) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="3" v-if="impostosNota.v_st">
                    <div class="text-caption text-medium-emphasis">Valor ICMS ST</div>
                    <div class="text-body-1 font-weight-bold">R$ {{ formatCurrency(impostosNota.v_st) }}</div>
                  </v-col>
                </v-row>

                <!-- PIS/COFINS/IPI -->
                <v-row class="mb-4">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-calculator-variant</v-icon>
                      PIS, COFINS e IPI
                    </h3>
                  </v-col>
                  <v-col cols="6" sm="4" md="2">
                    <div class="text-caption text-medium-emphasis">PIS</div>
                    <div class="text-body-1 font-weight-bold">R$ {{ formatCurrency(impostosNota.v_pis) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="2">
                    <div class="text-caption text-medium-emphasis">COFINS</div>
                    <div class="text-body-1 font-weight-bold">R$ {{ formatCurrency(impostosNota.v_cofins) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="2">
                    <div class="text-caption text-medium-emphasis">IPI</div>
                    <div class="text-body-1 font-weight-bold">R$ {{ formatCurrency(impostosNota.v_ipi) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="2" v-if="impostosNota.v_ii">
                    <div class="text-caption text-medium-emphasis">Importação</div>
                    <div class="text-body-1 font-weight-bold">R$ {{ formatCurrency(impostosNota.v_ii) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="2" v-if="impostosNota.v_frete">
                    <div class="text-caption text-medium-emphasis">Frete</div>
                    <div class="text-body-1">R$ {{ formatCurrency(impostosNota.v_frete) }}</div>
                  </v-col>
                  <v-col cols="6" sm="4" md="2" v-if="impostosNota.v_seg">
                    <div class="text-caption text-medium-emphasis">Seguro</div>
                    <div class="text-body-1">R$ {{ formatCurrency(impostosNota.v_seg) }}</div>
                  </v-col>
                </v-row>

                <!-- Impostos por Item -->
                <v-row v-if="impostosItens && impostosItens.length > 0">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
                      Impostos por Item
                    </h3>
                    <v-expansion-panels>
                      <v-expansion-panel
                        v-for="item in impostosItens"
                        :key="item.numero_item"
                      >
                        <v-expansion-panel-title>
                          <div>
                            <strong>Item {{ item.numero_item }}</strong> - {{ item.descricao_produto || 'N/A' }}
                          </div>
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <v-row>
                            <!-- ICMS -->
                            <v-col cols="12" v-if="item.icms_v_icms || item.icms_cst">
                              <v-divider class="mb-2"></v-divider>
                              <strong class="text-subtitle-2">ICMS</strong>
                              <v-row class="mt-2">
                                <v-col cols="6" sm="3">
                                  <div class="text-caption">CST</div>
                                  <div class="text-body-2">{{ item.icms_cst || 'N/A' }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.icms_v_bc">
                                  <div class="text-caption">Base Cálculo</div>
                                  <div class="text-body-2">R$ {{ formatCurrency(item.icms_v_bc) }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.icms_p_icms">
                                  <div class="text-caption">Alíquota</div>
                                  <div class="text-body-2">{{ formatPercent(item.icms_p_icms) }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.icms_v_icms">
                                  <div class="text-caption">Valor ICMS</div>
                                  <div class="text-body-2 font-weight-bold">R$ {{ formatCurrency(item.icms_v_icms) }}</div>
                                </v-col>
                              </v-row>
                            </v-col>

                            <!-- PIS -->
                            <v-col cols="12" v-if="item.pis_v_pis || item.pis_cst">
                              <v-divider class="mb-2"></v-divider>
                              <strong class="text-subtitle-2">PIS</strong>
                              <v-row class="mt-2">
                                <v-col cols="6" sm="3">
                                  <div class="text-caption">CST</div>
                                  <div class="text-body-2">{{ item.pis_cst || 'N/A' }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.pis_v_bc">
                                  <div class="text-caption">Base Cálculo</div>
                                  <div class="text-body-2">R$ {{ formatCurrency(item.pis_v_bc) }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.pis_p_pis">
                                  <div class="text-caption">Alíquota</div>
                                  <div class="text-body-2">{{ formatPercent(item.pis_p_pis) }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.pis_v_pis">
                                  <div class="text-caption">Valor PIS</div>
                                  <div class="text-body-2 font-weight-bold">R$ {{ formatCurrency(item.pis_v_pis) }}</div>
                                </v-col>
                              </v-row>
                            </v-col>

                            <!-- COFINS -->
                            <v-col cols="12" v-if="item.cofins_v_cofins || item.cofins_cst">
                              <v-divider class="mb-2"></v-divider>
                              <strong class="text-subtitle-2">COFINS</strong>
                              <v-row class="mt-2">
                                <v-col cols="6" sm="3">
                                  <div class="text-caption">CST</div>
                                  <div class="text-body-2">{{ item.cofins_cst || 'N/A' }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.cofins_v_bc">
                                  <div class="text-caption">Base Cálculo</div>
                                  <div class="text-body-2">R$ {{ formatCurrency(item.cofins_v_bc) }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.cofins_p_cofins">
                                  <div class="text-caption">Alíquota</div>
                                  <div class="text-body-2">{{ formatPercent(item.cofins_p_cofins) }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.cofins_v_cofins">
                                  <div class="text-caption">Valor COFINS</div>
                                  <div class="text-body-2 font-weight-bold">R$ {{ formatCurrency(item.cofins_v_cofins) }}</div>
                                </v-col>
                              </v-row>
                            </v-col>

                            <!-- IPI -->
                            <v-col cols="12" v-if="item.ipi_v_ipi || item.ipi_cst">
                              <v-divider class="mb-2"></v-divider>
                              <strong class="text-subtitle-2">IPI</strong>
                              <v-row class="mt-2">
                                <v-col cols="6" sm="3">
                                  <div class="text-caption">CST</div>
                                  <div class="text-body-2">{{ item.ipi_cst || 'N/A' }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.ipi_v_bc">
                                  <div class="text-caption">Base Cálculo</div>
                                  <div class="text-body-2">R$ {{ formatCurrency(item.ipi_v_bc) }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.ipi_p_ipi">
                                  <div class="text-caption">Alíquota</div>
                                  <div class="text-body-2">{{ formatPercent(item.ipi_p_ipi) }}</div>
                                </v-col>
                                <v-col cols="6" sm="3" v-if="item.ipi_v_ipi">
                                  <div class="text-caption">Valor IPI</div>
                                  <div class="text-body-2 font-weight-bold">R$ {{ formatCurrency(item.ipi_v_ipi) }}</div>
                                </v-col>
                              </v-row>
                            </v-col>
                          </v-row>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-col>
                </v-row>
              </div>

              <!-- Sem Dados -->
              <div v-else class="text-center py-8">
                <v-icon size="64" color="grey">mdi-file-document-remove</v-icon>
                <p class="text-body-1 text-medium-emphasis mt-4">
                  Dados de impostos não disponíveis no XML desta nota fiscal.
                </p>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- Análise Fiscal -->
      <v-row class="mt-4" v-if="analiseFiscal || loadingAnalise">
        <v-col cols="12">
          <v-card elevation="2">
            <v-card-title class="bg-purple text-white">
              <v-icon class="mr-2">mdi-calculator</v-icon>
              Análise Fiscal
            </v-card-title>
            <v-card-text>
              <!-- Loading -->
              <div v-if="loadingAnalise" class="text-center py-8">
                <v-progress-circular
                  indeterminate
                  color="primary"
                  size="48"
                ></v-progress-circular>
                <p class="mt-4">Carregando análise fiscal...</p>
              </div>

              <!-- Em Processamento -->
              <div v-else-if="analiseFiscal && analiseFiscal.em_processamento" class="text-center py-8">
                <v-icon size="64" color="warning">mdi-clock-outline</v-icon>
                <p class="text-h6 mt-4">Em Processamento</p>
                <p class="text-body-2 text-medium-emphasis">
                  A análise fiscal desta nota está sendo processada. Por favor, aguarde.
                </p>
              </div>

              <!-- Dados da Análise -->
              <div v-else-if="analiseFiscal">
                <!-- PIS/COFINS -->
                <v-row class="mb-4">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-percent</v-icon>
                      PIS/COFINS
                    </h3>
                    <v-row>
                      <v-col cols="12" sm="6" md="3">
                        <div class="text-caption text-medium-emphasis">Regime</div>
                        <div class="text-body-2 font-weight-medium">{{ analiseFiscal.regime_pis_cofins || 'N/A' }}</div>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <div class="text-caption text-medium-emphasis">Base de Cálculo</div>
                        <div class="text-body-2 font-weight-medium">R$ {{ formatCurrency(analiseFiscal.base_calculo_pis_cofins) }}</div>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <div class="text-caption text-medium-emphasis">Alíquota PIS</div>
                        <div class="text-body-2 font-weight-medium">{{ formatPercent(analiseFiscal.aliquota_pis) }}</div>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <div class="text-caption text-medium-emphasis">Alíquota COFINS</div>
                        <div class="text-body-2 font-weight-medium">{{ formatPercent(analiseFiscal.aliquota_cofins) }}</div>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <div class="text-caption text-medium-emphasis">Valor PIS Estimado</div>
                        <div class="text-body-2 font-weight-bold text-success">R$ {{ formatCurrency(analiseFiscal.valor_pis_estimado) }}</div>
                      </v-col>
                      <v-col cols="12" sm="6" md="3">
                        <div class="text-caption text-medium-emphasis">Valor COFINS Estimado</div>
                        <div class="text-body-2 font-weight-bold text-success">R$ {{ formatCurrency(analiseFiscal.valor_cofins_estimado) }}</div>
                      </v-col>
                    </v-row>
                    <v-alert v-if="analiseFiscal.observacoes_pis_cofins" type="info" variant="tonal" class="mt-3">
                      {{ analiseFiscal.observacoes_pis_cofins }}
                    </v-alert>
                  </v-col>
                </v-row>

                <v-divider class="my-4"></v-divider>

                <!-- ICMS -->
                <v-row class="mb-4">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-file-document-outline</v-icon>
                      ICMS
                    </h3>
                    <v-row>
                      <v-col cols="12" sm="6" md="4">
                        <div class="text-caption text-medium-emphasis">Valor Total ICMS</div>
                        <div class="text-body-2 font-weight-bold text-primary">R$ {{ formatCurrency(analiseFiscal.valor_total_icms_destacado) }}</div>
                      </v-col>
                      <v-col cols="12" sm="6" md="4">
                        <div class="text-caption text-medium-emphasis">Potencial DIFAL</div>
                        <v-chip 
                          :color="analiseFiscal.potencial_difal ? 'warning' : 'success'"
                          size="small"
                          class="mt-1"
                        >
                          {{ analiseFiscal.potencial_difal ? 'Sim' : 'Não' }}
                        </v-chip>
                      </v-col>
                    </v-row>
                    <v-alert v-if="analiseFiscal.observacoes_difal" type="warning" variant="tonal" class="mt-3">
                      {{ analiseFiscal.observacoes_difal }}
                    </v-alert>
                  </v-col>
                </v-row>

                <v-divider class="my-4"></v-divider>

                <!-- ICMS por Item -->
                <v-row class="mb-4" v-if="analiseFiscal.icms_por_item && analiseFiscal.icms_por_item.length > 0">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-format-list-bulleted</v-icon>
                      ICMS por Item
                    </h3>
                    <v-table density="compact">
                      <thead>
                        <tr>
                          <th>Item</th>
                          <th>NCM</th>
                          <th>Base Cálculo</th>
                          <th>Alíquota</th>
                          <th>Valor ICMS</th>
                          <th>Situação</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="item in analiseFiscal.icms_por_item" :key="item.numero_item">
                          <td>{{ item.numero_item }}</td>
                          <td>{{ item.ncm }}</td>
                          <td>R$ {{ formatCurrency(item.base_calculo) }}</td>
                          <td>{{ formatPercent(item.aliquota_icms) }}</td>
                          <td>R$ {{ formatCurrency(item.valor_icms) }}</td>
                          <td>{{ item.situacao_icms }}</td>
                        </tr>
                      </tbody>
                    </v-table>
                  </v-col>
                </v-row>

                <v-divider class="my-4" v-if="analiseFiscal.recuperacao_credito"></v-divider>

                <!-- Recuperação de Crédito -->
                <v-row class="mb-4" v-if="analiseFiscal.recuperacao_credito">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-cash-refund</v-icon>
                      Oportunidades de Recuperação de Crédito
                    </h3>

                    <!-- ICMS -->
                    <v-card v-if="analiseFiscal.recuperacao_credito.oportunidades_potenciais?.icms" class="mb-3" variant="outlined">
                      <v-card-title class="text-subtitle-1 bg-blue-lighten-5">
                        <v-icon class="mr-2" color="blue">mdi-file-document</v-icon>
                        ICMS
                      </v-card-title>
                      <v-card-text>
                        <div v-if="analiseFiscal.recuperacao_credito.oportunidades_potenciais.icms.credito_direto_nfe_entrada">
                          <div class="font-weight-bold mb-2">Crédito Direto NF-e Entrada</div>
                          <v-row>
                            <v-col cols="12" sm="6">
                              <div class="text-caption text-medium-emphasis">Valor Potencial</div>
                              <div class="text-body-1 font-weight-bold text-success">
                                {{ analiseFiscal.recuperacao_credito.oportunidades_potenciais.icms.credito_direto_nfe_entrada.valor_potencial ? 
                                   'R$ ' + formatCurrency(analiseFiscal.recuperacao_credito.oportunidades_potenciais.icms.credito_direto_nfe_entrada.valor_potencial) : 
                                   'N/A' }}
                              </div>
                            </v-col>
                          </v-row>
                          <v-alert v-if="analiseFiscal.recuperacao_credito.oportunidades_potenciais.icms.credito_direto_nfe_entrada.condicoes" 
                                   type="info" variant="tonal" class="mt-3 text-body-2">
                            {{ analiseFiscal.recuperacao_credito.oportunidades_potenciais.icms.credito_direto_nfe_entrada.condicoes }}
                          </v-alert>
                        </div>
                      </v-card-text>
                    </v-card>

                    <!-- PIS/COFINS -->
                    <v-card v-if="analiseFiscal.recuperacao_credito.oportunidades_potenciais?.pis_cofins" class="mb-3" variant="outlined">
                      <v-card-title class="text-subtitle-1 bg-green-lighten-5">
                        <v-icon class="mr-2" color="green">mdi-percent</v-icon>
                        PIS/COFINS
                      </v-card-title>
                      <v-card-text>
                        <div v-if="analiseFiscal.recuperacao_credito.oportunidades_potenciais.pis_cofins.credito_regime_nao_cumulativo">
                          <div class="font-weight-bold mb-2">Crédito Regime Não Cumulativo</div>
                          <v-chip v-if="analiseFiscal.recuperacao_credito.oportunidades_potenciais.pis_cofins.credito_regime_nao_cumulativo.valor_potencial_indeterminado" 
                                  color="warning" size="small" class="mb-3">
                            Valor Potencial Indeterminado
                          </v-chip>
                          <v-alert v-if="analiseFiscal.recuperacao_credito.oportunidades_potenciais.pis_cofins.credito_regime_nao_cumulativo.condicoes" 
                                   type="info" variant="tonal" class="text-body-2">
                            {{ analiseFiscal.recuperacao_credito.oportunidades_potenciais.pis_cofins.credito_regime_nao_cumulativo.condicoes }}
                          </v-alert>
                        </div>
                      </v-card-text>
                    </v-card>

                    <!-- Outras Oportunidades -->
                    <v-card v-if="analiseFiscal.recuperacao_credito.oportunidades_potenciais?.outras_oportunidades?.length > 0" 
                            class="mb-3" variant="outlined">
                      <v-card-title class="text-subtitle-1 bg-purple-lighten-5">
                        <v-icon class="mr-2" color="purple">mdi-lightbulb-on</v-icon>
                        Outras Oportunidades
                      </v-card-title>
                      <v-card-text>
                        <v-list density="compact">
                          <v-list-item v-for="(oportunidade, index) in analiseFiscal.recuperacao_credito.oportunidades_potenciais.outras_oportunidades" 
                                       :key="index">
                            <template v-slot:prepend>
                              <v-icon color="purple">mdi-chevron-right</v-icon>
                            </template>
                            <v-list-item-title class="font-weight-bold">{{ oportunidade.tipo }}</v-list-item-title>
                            <v-list-item-subtitle class="text-wrap mt-1">{{ oportunidade.condicoes }}</v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>

                    <!-- Advertências e Limitações -->
                    <v-card v-if="analiseFiscal.recuperacao_credito.advertencias_limitacoes?.length > 0" 
                            variant="outlined" color="warning">
                      <v-card-title class="text-subtitle-1 bg-warning-lighten-4">
                        <v-icon class="mr-2" color="warning">mdi-alert</v-icon>
                        Advertências e Limitações
                      </v-card-title>
                      <v-card-text>
                        <v-list density="compact">
                          <v-list-item v-for="(advertencia, index) in analiseFiscal.recuperacao_credito.advertencias_limitacoes" 
                                       :key="index">
                            <template v-slot:prepend>
                              <v-icon color="warning" size="small">mdi-alert-circle</v-icon>
                            </template>
                            <v-list-item-subtitle class="text-wrap">{{ advertencia }}</v-list-item-subtitle>
                          </v-list-item>
                        </v-list>
                      </v-card-text>
                    </v-card>
                  </v-col>
                </v-row>

                <v-divider class="my-4" v-if="analiseFiscal.dados_completos"></v-divider>

                <!-- Dados Completos (JSON) -->
                <v-row class="mb-4" v-if="analiseFiscal.dados_completos">
                  <v-col cols="12">
                    <h3 class="text-h6 mb-3">
                      <v-icon class="mr-2">mdi-code-json</v-icon>
                      Análise Completa (JSON)
                    </h3>
                    <v-expansion-panels>
                      <v-expansion-panel>
                        <v-expansion-panel-title>
                          <v-icon class="mr-2">mdi-file-code</v-icon>
                          Ver JSON Completo
                        </v-expansion-panel-title>
                        <v-expansion-panel-text>
                          <pre class="text-body-2" style="white-space: pre-wrap; word-wrap: break-word; max-height: 500px; overflow-y: auto;">{{ JSON.stringify(analiseFiscal.dados_completos, null, 2) }}</pre>
                        </v-expansion-panel-text>
                      </v-expansion-panel>
                    </v-expansion-panels>
                  </v-col>
                </v-row>

                <!-- Dados Atualizados -->
                <v-row>
                  <v-col cols="12">
                    <div class="text-caption text-medium-emphasis">
                      Última atualização: {{ formatDate(analiseFiscal.data_atualizacao) }}
                    </div>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>
    </template>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()

// State
const nota = ref(null)
const itens = ref([])
const analiseFiscal = ref(null)
const impostosNota = ref(null)
const impostosItens = ref([])
const loading = ref(true)
const loadingItens = ref(true)
const loadingAnalise = ref(false)
const loadingImpostos = ref(false)
const error = ref(null)
const processingAnalysis = ref(false)
const analysisSuccess = ref(false)
const analysisError = ref(null)

// Headers para tabela de itens
const headers = [
  { title: 'Código', value: 'cprod', width: '100px' },
  { title: 'Produto', value: 'xprod' },
  { title: 'NCM', value: 'ncm', width: '100px' },
  { title: 'Qtd', value: 'qcom', width: '80px', align: 'end' },
  { title: 'Valor Unit.', value: 'vuncom', width: '120px', align: 'end' },
  { title: 'Valor Total', value: 'vprod', width: '120px', align: 'end' }
]

// Methods
async function loadNota() {
  loading.value = true
  error.value = null
  
  try {
    const chaveAcesso = route.params.chaveAcesso
    const response = await axios.get(`/api/notas/${chaveAcesso}`)
    nota.value = response.data.nota
    itens.value = response.data.itens || []
    
    // Carregar análise fiscal
    loadAnaliseFiscal(chaveAcesso)
    
    // Carregar impostos do XML
    loadImpostos(chaveAcesso)
  } catch (err) {
    console.error('Erro ao carregar nota:', err)
    error.value = err.response?.data?.detail || 'Não foi possível carregar a nota fiscal'
  } finally {
    loading.value = false
    loadingItens.value = false
  }
}

async function loadImpostos(chaveAcesso) {
  loadingImpostos.value = true
  
  try {
    console.log('💰 Carregando impostos para:', chaveAcesso)
    const response = await axios.get(`/api/load/impostos/completo/${chaveAcesso}`)
    console.log('📊 Resposta de impostos:', response.data)
    
    impostosNota.value = response.data.impostos_nota
    impostosItens.value = response.data.impostos_itens || []
    console.log('✅ Impostos carregados')
  } catch (err) {
    console.error('❌ Erro ao carregar impostos:', err)
    // Não mostrar erro crítico se impostos não existirem
    impostosNota.value = null
    impostosItens.value = []
  } finally {
    loadingImpostos.value = false
  }
}

async function loadAnaliseFiscal(chaveAcesso) {
  loadingAnalise.value = true
  
  try {
    console.log('🔍 Carregando análise fiscal para:', chaveAcesso)
    const response = await axios.get(`/taxes/analise_fiscal/${chaveAcesso}`)
    console.log('📊 Resposta da análise fiscal:', response.data)
    
    if (response.data.found) {
      analiseFiscal.value = response.data.analise
      console.log('✅ Análise fiscal carregada:', analiseFiscal.value)
    } else {
      analiseFiscal.value = null
      console.log('⚠️ Análise fiscal não encontrada')
    }
  } catch (err) {
    console.error('❌ Erro ao carregar análise fiscal:', err)
    analiseFiscal.value = null
  } finally {
    loadingAnalise.value = false
  }
}

async function iniciarAnaliseFiscal() {
  processingAnalysis.value = true
  analysisSuccess.value = false
  analysisError.value = null
  
  try {
    const chaveAcesso = route.params.chaveAcesso
    console.log('🚀 Iniciando análise fiscal para:', chaveAcesso)
    
    // Marcar como "Em Processamento" antes de enviar para cálculo
    await axios.put('/taxes/analise_fiscal/processamento', {
      chave_acesso: chaveAcesso,
      em_processamento: true
    })
    
    // Recarregar análise para mostrar "Em Processamento"
    await loadAnaliseFiscal(chaveAcesso)
    
    // Enviar para cálculo de impostos
    const response = await axios.post('/taxes/calculate-taxes/', {
      chave_acesso: chaveAcesso
    })
    
    console.log('✅ Análise fiscal iniciada:', response.data)
    analysisSuccess.value = true
    
    // Recarregar análise após 3 segundos para atualizar a página
    setTimeout(() => {
      loadAnaliseFiscal(chaveAcesso)
    }, 3000)
    
  } catch (err) {
    console.error('❌ Erro ao iniciar análise fiscal:', err)
    analysisError.value = err.response?.data?.detail || 'Não foi possível iniciar a análise fiscal'
  } finally {
    processingAnalysis.value = false
  }
}

function formatDate(dateString) {
  if (!dateString) return 'N/A'
  const date = new Date(dateString)
  return new Intl.DateTimeFormat('pt-BR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  }).format(date)
}

function formatCurrency(value) {
  if (!value) return '0,00'
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

function formatNumber(value) {
  if (!value) return '0'
  return new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value)
}

function formatCNPJ(cnpj) {
  if (!cnpj) return 'N/A'
  return cnpj.replace(/^(\d{2})(\d{3})(\d{3})(\d{4})(\d{2})$/, '$1.$2.$3/$4-$5')
}

function formatCPF(cpf) {
  if (!cpf) return 'N/A'
  return cpf.replace(/^(\d{3})(\d{3})(\d{3})(\d{2})$/, '$1.$2.$3-$4')
}

function getClassificacaoColor(classificacao) {
  switch (classificacao) {
    case 'COMPRA': return 'blue'
    case 'VENDA': return 'green'
    case 'SERVICO': return 'orange'
    default: return 'grey'
  }
}

function formatPercent(value) {
  if (!value) return '0%'
  return `${value}%`
}

// Lifecycle
onMounted(() => {
  loadNota()
})
</script>

<style scoped>
.v-container {
  min-height: calc(100vh - 64px);
}
</style>


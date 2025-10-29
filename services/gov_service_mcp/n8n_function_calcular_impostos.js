// Exemplo completo de Function Node para calcular impostos
// Use este código em um "Code" node no n8n após receber dados do MCP

// ============================================
// FUNÇÃO: Calcular Impostos de uma Nota Fiscal
// ============================================

// Input esperado:
// - Nota fiscal com itens
// - Dados NCM e ICMS do MCP

const notaFiscal = $input.first().json;
const itensComImpostos = [];

// Processar cada item da nota fiscal
for (const item of notaFiscal.itens) {
  // Aqui você já deve ter consultado NCM e ICMS via MCP
  // Vamos assumir que os dados estão disponíveis
  
  const valorBase = parseFloat(item.valor_produto);
  
  // Dados vindos do MCP
  const ncmData = item.ncm_data; // Da consulta MCP NCM
  const icmsData = item.icms_data; // Da consulta MCP ICMS
  
  // ========================================
  // 1. CALCULAR PIS/COFINS
  // ========================================
  let valorPis = 0;
  let valorCofins = 0;
  
  if (ncmData.tributacao_pis_cofins.regime_especial === "Nenhum") {
    valorPis = valorBase * (ncmData.tributacao_pis_cofins.aliquota_pis_padrao / 100);
    valorCofins = valorBase * (ncmData.tributacao_pis_cofins.aliquota_cofins_padrao / 100);
  } else if (ncmData.tributacao_pis_cofins.regime_especial === "Monofasico") {
    // PIS/COFINS monofásico - já foi recolhido na indústria
    valorPis = 0;
    valorCofins = 0;
  } else if (ncmData.tributacao_pis_cofins.regime_especial === "Aliquota_Zero") {
    valorPis = 0;
    valorCofins = 0;
  }
  
  // ========================================
  // 2. CALCULAR IPI
  // ========================================
  const valorIpi = valorBase * (ncmData.aliquota_ipi_padrao / 100);
  
  // ========================================
  // 3. CALCULAR ICMS
  // ========================================
  let valorIcms = 0;
  let valorIcmsSt = 0;
  
  if (icmsData.icms_st_aplicavel) {
    // ICMS com Substituição Tributária
    const baseCalculoSt = valorBase * (1 + icmsData.mva_original_icms_st / 100);
    valorIcmsSt = baseCalculoSt * (icmsData.aliquota_interna_destino / 100);
    valorIcms = 0; // Na ST, o ICMS é recolhido antecipadamente
  } else {
    // ICMS Normal
    valorIcms = valorBase * (icmsData.aliquota_interestadual / 100);
  }
  
  // ========================================
  // 4. CALCULAR DIFAL (para consumidor final não contribuinte)
  // ========================================
  let valorDifal = 0;
  let valorDifalOrigemPartilha = 0;
  let valorDifalDestinoPartilha = 0;
  
  if (icmsData.uf_origem !== icmsData.uf_destino && 
      icmsData.aliquota_difal_destino > 0) {
    
    const diferencaAliquota = icmsData.aliquota_difal_destino - icmsData.aliquota_interestadual;
    valorDifal = valorBase * (diferencaAliquota / 100);
    
    // Partilha entre origem e destino
    valorDifalOrigemPartilha = valorDifal * (icmsData.partilha_difal_origem / 100);
    valorDifalDestinoPartilha = valorDifal * (icmsData.partilha_difal_destino / 100);
  }
  
  // ========================================
  // 5. CALCULAR FCP (Fundo de Combate à Pobreza)
  // ========================================
  let valorFcp = 0;
  if (icmsData.aliquota_fcp_destino > 0) {
    valorFcp = valorBase * (icmsData.aliquota_fcp_destino / 100);
  }
  
  // ========================================
  // 6. TOTALIZADORES
  // ========================================
  const totalTributos = valorPis + valorCofins + valorIpi + valorIcms + 
                        valorIcmsSt + valorDifal + valorFcp;
  
  const valorTotalItem = valorBase + valorIpi + valorIcmsSt + valorFcp;
  
  const cargaTributaria = (totalTributos / valorBase) * 100;
  
  // ========================================
  // 7. MONTAR OBJETO DE RETORNO
  // ========================================
  itensComImpostos.push({
    // Dados do item
    numero_item: item.numero_item,
    codigo_produto: item.codigo_produto,
    descricao: item.descricao,
    ncm: item.ncm,
    descricao_ncm: ncmData.descricao,
    quantidade: item.quantidade,
    valor_unitario: item.valor_unitario,
    valor_base: valorBase,
    
    // Tributos calculados
    tributos: {
      pis: {
        regime: ncmData.tributacao_pis_cofins.regime_especial,
        aliquota: ncmData.tributacao_pis_cofins.aliquota_pis_padrao,
        base_calculo: valorBase,
        valor: valorPis
      },
      cofins: {
        regime: ncmData.tributacao_pis_cofins.regime_especial,
        aliquota: ncmData.tributacao_pis_cofins.aliquota_cofins_padrao,
        base_calculo: valorBase,
        valor: valorCofins
      },
      ipi: {
        aliquota: ncmData.aliquota_ipi_padrao,
        base_calculo: valorBase,
        valor: valorIpi
      },
      icms: {
        regime: icmsData.regime_icms_para_ncm,
        uf_origem: icmsData.uf_origem,
        uf_destino: icmsData.uf_destino,
        aliquota_interna_origem: icmsData.aliquota_interna_origem,
        aliquota_interna_destino: icmsData.aliquota_interna_destino,
        aliquota_interestadual: icmsData.aliquota_interestadual,
        base_calculo: valorBase,
        valor: valorIcms,
        
        // Substituição Tributária
        st_aplicavel: icmsData.icms_st_aplicavel,
        mva: icmsData.mva_original_icms_st,
        base_calculo_st: icmsData.icms_st_aplicavel ? 
          valorBase * (1 + icmsData.mva_original_icms_st / 100) : 0,
        valor_st: valorIcmsSt
      },
      difal: {
        aplicavel: valorDifal > 0,
        diferenca_aliquota: icmsData.aliquota_difal_destino - icmsData.aliquota_interestadual,
        base_calculo: valorBase,
        valor_total: valorDifal,
        partilha: {
          origem: {
            percentual: icmsData.partilha_difal_origem,
            valor: valorDifalOrigemPartilha
          },
          destino: {
            percentual: icmsData.partilha_difal_destino,
            valor: valorDifalDestinoPartilha
          }
        }
      },
      fcp: {
        aplicavel: valorFcp > 0,
        aliquota: icmsData.aliquota_fcp_destino,
        base_calculo: valorBase,
        valor: valorFcp
      }
    },
    
    // Totalizadores
    totais: {
      total_tributos_federais: valorPis + valorCofins + valorIpi,
      total_tributos_estaduais: valorIcms + valorIcmsSt + valorDifal + valorFcp,
      total_geral_tributos: totalTributos,
      valor_total_item: valorTotalItem,
      carga_tributaria_percentual: parseFloat(cargaTributaria.toFixed(2))
    }
  });
}

// ========================================
// 8. TOTALIZAR NOTA FISCAL
// ========================================
const totaisNota = itensComImpostos.reduce((acc, item) => {
  return {
    valor_base_total: acc.valor_base_total + item.valor_base,
    pis_total: acc.pis_total + item.tributos.pis.valor,
    cofins_total: acc.cofins_total + item.tributos.cofins.valor,
    ipi_total: acc.ipi_total + item.tributos.ipi.valor,
    icms_total: acc.icms_total + item.tributos.icms.valor,
    icms_st_total: acc.icms_st_total + item.tributos.icms.valor_st,
    difal_total: acc.difal_total + item.tributos.difal.valor_total,
    fcp_total: acc.fcp_total + item.tributos.fcp.valor,
    tributos_totais: acc.tributos_totais + item.totais.total_geral_tributos,
    valor_total_nf: acc.valor_total_nf + item.totais.valor_total_item
  };
}, {
  valor_base_total: 0,
  pis_total: 0,
  cofins_total: 0,
  ipi_total: 0,
  icms_total: 0,
  icms_st_total: 0,
  difal_total: 0,
  fcp_total: 0,
  tributos_totais: 0,
  valor_total_nf: 0
});

// Carga tributária média
totaisNota.carga_tributaria_media = 
  (totaisNota.tributos_totais / totaisNota.valor_base_total) * 100;

// ========================================
// 9. RETORNAR RESULTADO
// ========================================
return [{
  json: {
    chave_nf: notaFiscal.chave_acesso,
    numero_nf: notaFiscal.numero_nf,
    emitente: notaFiscal.emitente,
    destinatario: notaFiscal.destinatario,
    data_emissao: notaFiscal.data_emissao,
    
    itens: itensComImpostos,
    
    totais_nota: {
      quantidade_itens: itensComImpostos.length,
      valor_produtos: parseFloat(totaisNota.valor_base_total.toFixed(2)),
      valor_pis: parseFloat(totaisNota.pis_total.toFixed(2)),
      valor_cofins: parseFloat(totaisNota.cofins_total.toFixed(2)),
      valor_ipi: parseFloat(totaisNota.ipi_total.toFixed(2)),
      valor_icms: parseFloat(totaisNota.icms_total.toFixed(2)),
      valor_icms_st: parseFloat(totaisNota.icms_st_total.toFixed(2)),
      valor_difal: parseFloat(totaisNota.difal_total.toFixed(2)),
      valor_fcp: parseFloat(totaisNota.fcp_total.toFixed(2)),
      total_tributos: parseFloat(totaisNota.tributos_totais.toFixed(2)),
      total_nota_fiscal: parseFloat(totaisNota.valor_total_nf.toFixed(2)),
      carga_tributaria_percentual: parseFloat(totaisNota.carga_tributaria_media.toFixed(2))
    },
    
    processamento: {
      data_calculo: new Date().toISOString(),
      versao_calculo: "1.0.0",
      fonte_dados: "gov-service-mcp"
    }
  }
}];


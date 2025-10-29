#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Servidor MCP personalizado para geração de gráficos usando Plotly
VERSÃO INTERATIVA - Gera HTML interativo em vez de imagens estáticas
Expõe ferramentas: generate_pie_chart, generate_bar_chart, generate_column_chart, generate_line_chart, 
generate_area_chart, generate_histogram, generate_box_plot, generate_distribution_plot, 
generate_scatter_plot, generate_heatmap
"""

import asyncio
import logging
import sys
from typing import List, Union, Optional, Dict, Any
import json
from datetime import datetime

import plotly.graph_objects as go
import plotly.io as pio

from mcp.server import Server
from mcp.types import Tool, TextContent
import mcp.server.stdio

# Logging apenas em stderr
logging.basicConfig(level=logging.INFO, stream=sys.stderr, force=True)
logger = logging.getLogger("mcp-chart-server-interactive")

server = Server("plotly-chart-server-interactive")


def _fig_to_json_data(fig: go.Figure) -> dict:
    """Converte figure do Plotly para dados JSON para renderização no frontend"""
    # Extrai dados e layout da figura
    fig_dict = fig.to_dict()
    
    return {
        "type": "plotly_chart",
        "data": fig_dict.get("data", []),
        "layout": fig_dict.get("layout", {}),
        "config": {
            "displayModeBar": True,
            "displaylogo": False,
            "modeBarButtonsToRemove": ['pan2d', 'lasso2d', 'select2d'],
            "responsive": True
        }
    }


def _format_pairs(pairs: List[tuple[str, Union[str, float]]]) -> str:
    return "\n".join([f"• {k}: {v}" for k, v in pairs])


@server.list_tools()
async def list_tools() -> List[Tool]:
    """Lista todas as ferramentas disponíveis"""
    return [
        Tool(
            name="generate_pie_chart",
            description="Gera um gráfico de pizza interativo usando Plotly",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["category", "value"]
                        },
                        "description": "Lista de dicionários com 'category' e 'value'"
                    },
                    "title": {
                        "type": "string",
                        "default": "Gráfico de Pizza",
                        "description": "Título do gráfico"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_bar_chart",
            description="Gera um gráfico de barras interativo usando Plotly",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["category", "value"]
                        },
                        "description": "Lista de dicionários com 'category' e 'value'"
                    },
                    "title": {
                        "type": "string",
                        "default": "Gráfico de Barras",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "Categorias",
                        "description": "Label do eixo X"
                    },
                    "y_label": {
                        "type": "string",
                        "default": "Valores",
                        "description": "Label do eixo Y"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_line_chart",
            description="Gera um gráfico de linha interativo usando Plotly",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["category", "value"]
                        },
                        "description": "Lista de dicionários com 'category' (x) e 'value' (y)"
                    },
                    "title": {
                        "type": "string",
                        "default": "Gráfico de Linha",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "X",
                        "description": "Label do eixo X"
                    },
                    "y_label": {
                        "type": "string",
                        "default": "Y",
                        "description": "Label do eixo Y"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_area_chart",
            description="Gera um gráfico de área interativo usando Plotly",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["category", "value"]
                        },
                        "description": "Lista de dicionários com 'category' (x) e 'value' (y)"
                    },
                    "title": {
                        "type": "string",
                        "default": "Gráfico de Área",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "X",
                        "description": "Label do eixo X"
                    },
                    "y_label": {
                        "type": "string",
                        "default": "Y",
                        "description": "Label do eixo Y"
                    },
                    "fill_color": {
                        "type": "string",
                        "default": "rgba(26, 118, 255, 0.3)",
                        "description": "Cor de preenchimento da área (RGBA)"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_column_chart",
            description="Gera um gráfico de colunas interativo usando Plotly",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["category", "value"]
                        },
                        "description": "Lista de dicionários com 'category' e 'value'"
                    },
                    "title": {
                        "type": "string",
                        "default": "Gráfico de Colunas",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "Categorias",
                        "description": "Label do eixo X"
                    },
                    "y_label": {
                        "type": "string",
                        "default": "Valores",
                        "description": "Label do eixo Y"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_histogram",
            description="Gera um histograma interativo usando Plotly para mostrar distribuição de valores",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Lista de valores numéricos para criar o histograma"
                    },
                    "title": {
                        "type": "string",
                        "default": "Histograma",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "Valores",
                        "description": "Label do eixo X"
                    },
                    "y_label": {
                        "type": "string",
                        "default": "Frequência",
                        "description": "Label do eixo Y"
                    },
                    "nbins": {
                        "type": "integer",
                        "default": 20,
                        "description": "Número de bins (barras) do histograma"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_box_plot",
            description="Gera um box plot interativo usando Plotly para análise estatística",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "category": {"type": "string"},
                                "value": {"type": "number"}
                            },
                            "required": ["category", "value"]
                        },
                        "description": "Lista de dicionários com 'category' e 'value' para box plot por categoria"
                    },
                    "title": {
                        "type": "string",
                        "default": "Box Plot",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "Categorias",
                        "description": "Label do eixo X"
                    },
                    "y_label": {
                        "type": "string",
                        "default": "Valores",
                        "description": "Label do eixo Y"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_distribution_plot",
            description="Gera um gráfico de distribuição (histograma + curva de densidade) usando Plotly",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Lista de valores numéricos para análise de distribuição"
                    },
                    "title": {
                        "type": "string",
                        "default": "Gráfico de Distribuição",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "Valores",
                        "description": "Label do eixo X"
                    },
                    "show_hist": {
                        "type": "boolean",
                        "default": True,
                        "description": "Mostrar histograma"
                    },
                    "show_curve": {
                        "type": "boolean",
                        "default": True,
                        "description": "Mostrar curva de densidade"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_scatter_plot",
            description="Gera um gráfico de dispersão interativo usando Plotly para análise de correlação",
            inputSchema={
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "x": {"type": "number"},
                                "y": {"type": "number"},
                                "category": {"type": "string"}
                            },
                            "required": ["x", "y"]
                        },
                        "description": "Lista de pontos com coordenadas x, y e categoria opcional"
                    },
                    "title": {
                        "type": "string",
                        "default": "Gráfico de Dispersão",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "Eixo X",
                        "description": "Label do eixo X"
                    },
                    "y_label": {
                        "type": "string",
                        "default": "Eixo Y",
                        "description": "Label do eixo Y"
                    },
                    "color_by_category": {
                        "type": "boolean",
                        "default": False,
                        "description": "Colorir pontos por categoria"
                    },
                    "show_trendline": {
                        "type": "boolean",
                        "default": False,
                        "description": "Mostrar linha de tendência"
                    },
                    "point_size": {
                        "type": "integer",
                        "default": 8,
                        "description": "Tamanho dos pontos"
                    }
                },
                "required": ["data"]
            }
        ),
        Tool(
            name="generate_heatmap",
            description="Gera um heatmap (mapa de calor) interativo usando Plotly. Ideal para visualizar correlações, matrizes de dados ou padrões em dados bidimensionais",
            inputSchema={
                "type": "object",
                "properties": {
                    "z_data": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"}
                        },
                        "description": "Matriz 2D de valores numéricos (lista de listas)"
                    },
                    "x_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels para o eixo X (opcional)"
                    },
                    "y_labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels para o eixo Y (opcional)"
                    },
                    "title": {
                        "type": "string",
                        "default": "Heatmap",
                        "description": "Título do gráfico"
                    },
                    "x_label": {
                        "type": "string",
                        "default": "X",
                        "description": "Label do eixo X"
                    },
                    "y_label": {
                        "type": "string",
                        "default": "Y",
                        "description": "Label do eixo Y"
                    },
                    "colorscale": {
                        "type": "string",
                        "default": "Viridis",
                        "description": "Escala de cores (Viridis, RdBu, Blues, Reds, Greens, YlOrRd, etc.)"
                    },
                    "show_values": {
                        "type": "boolean",
                        "default": True,
                        "description": "Mostrar valores nas células do heatmap"
                    },
                    "colorbar_title": {
                        "type": "string",
                        "default": "Valor",
                        "description": "Título da barra de cores"
                    }
                },
                "required": ["z_data"]
            }
        )
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> List[TextContent]:
    """Executa uma ferramenta específica"""
    
    if name == "generate_pie_chart":
        return await generate_pie_chart(
            arguments.get("data", []),
            arguments.get("title", "Gráfico de Pizza")
        )
    elif name == "generate_bar_chart":
        return await generate_bar_chart(
            arguments.get("data", []),
            arguments.get("title", "Gráfico de Barras"),
            arguments.get("x_label", "Categorias"),
            arguments.get("y_label", "Valores")
        )
    elif name == "generate_line_chart":
        return await generate_line_chart(
            arguments.get("data", []),
            arguments.get("title", "Gráfico de Linha"),
            arguments.get("x_label", "X"),
            arguments.get("y_label", "Y")
        )
    elif name == "generate_area_chart":
        return await generate_area_chart(
            arguments.get("data", []),
            arguments.get("title", "Gráfico de Área"),
            arguments.get("x_label", "X"),
            arguments.get("y_label", "Y"),
            arguments.get("fill_color", "rgba(26, 118, 255, 0.3)")
        )
    elif name == "generate_column_chart":
        return await generate_column_chart(
            arguments.get("data", []),
            arguments.get("title", "Gráfico de Colunas"),
            arguments.get("x_label", "Categorias"),
            arguments.get("y_label", "Valores")
        )
    elif name == "generate_histogram":
        return await generate_histogram(
            arguments.get("data", []),
            arguments.get("title", "Histograma"),
            arguments.get("x_label", "Valores"),
            arguments.get("y_label", "Frequência"),
            arguments.get("nbins", 20)
        )
    elif name == "generate_box_plot":
        return await generate_box_plot(
            arguments.get("data", []),
            arguments.get("title", "Box Plot"),
            arguments.get("x_label", "Categorias"),
            arguments.get("y_label", "Valores")
        )
    elif name == "generate_distribution_plot":
        return await generate_distribution_plot(
            arguments.get("data", []),
            arguments.get("title", "Gráfico de Distribuição"),
            arguments.get("x_label", "Valores"),
            arguments.get("show_hist", True),
            arguments.get("show_curve", True)
        )
    elif name == "generate_scatter_plot":
        return await generate_scatter_plot(
            arguments.get("data", []),
            arguments.get("title", "Gráfico de Dispersão"),
            arguments.get("x_label", "Eixo X"),
            arguments.get("y_label", "Eixo Y"),
            arguments.get("color_by_category", False),
            arguments.get("show_trendline", False),
            arguments.get("point_size", 8)
        )
    elif name == "generate_heatmap":
        return await generate_heatmap(
            arguments.get("z_data", []),
            arguments.get("x_labels"),
            arguments.get("y_labels"),
            arguments.get("title", "Heatmap"),
            arguments.get("x_label", "X"),
            arguments.get("y_label", "Y"),
            arguments.get("colorscale", "Viridis"),
            arguments.get("show_values", True),
            arguments.get("colorbar_title", "Valor")
        )
    else:
        raise ValueError(f"Ferramenta desconhecida: {name}")


async def generate_pie_chart(
    data: List[Dict[str, Union[str, float]]],
    title: str = "Gráfico de Pizza"
) -> List[TextContent]:
    """Gera um gráfico de pizza interativo usando Plotly"""
    try:
        logger.info(f"🥧 Gerando gráfico de pizza: {title}")
        
        categories = [item['category'] for item in data]
        values = [float(item['value']) for item in data]
        
        fig = go.Figure(data=[
            go.Pie(
                labels=categories,
                values=values,
                hole=0.3,
                hovertemplate='<b>%{label}</b><br>Valor: %{value}<br>Percentual: %{percent}<extra></extra>',
                textinfo='label+percent',
                textposition='auto'
            )
        ])
        
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            showlegend=True,
            width=800,
            height=600,
            margin=dict(t=100, b=50, l=50, r=50)
        )
        
        chart_data = _fig_to_json_data(fig)
        pairs = [(item['category'], item['value']) for item in data]
        summary = _format_pairs(pairs)
        
        result = f"""📊 **{title}** gerado com sucesso!

**Dados:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Gráfico interativo com hover, zoom, pan e outras funcionalidades.*"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar gráfico de pizza: {e}")
        return [TextContent(type="text", text=f"❌ Erro ao gerar gráfico de pizza: {str(e)}")]


async def generate_bar_chart(
    data: List[Dict[str, Union[str, float]]],
    title: str = "Gráfico de Barras",
    x_label: str = "Categorias",
    y_label: str = "Valores"
) -> List[TextContent]:
    """Gera um gráfico de barras interativo usando Plotly"""
    try:
        logger.info(f"📊 Gerando gráfico de barras: {title}")
        
        categories = [item['category'] for item in data]
        values = [float(item['value']) for item in data]
        
        fig = go.Figure(data=[
            go.Bar(
                x=categories,
                y=values,
                hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>',
                marker_color='rgb(26, 118, 255)',
                marker_line_color='rgb(8, 48, 107)',
                marker_line_width=1.5
            )
        ])
        
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            xaxis_title=x_label,
            yaxis_title=y_label,
            width=800,
            height=600,
            margin=dict(t=100, b=100, l=80, r=50),
            hovermode='x unified'
        )
        
        chart_data = _fig_to_json_data(fig)
        pairs = [(item['category'], item['value']) for item in data]
        summary = _format_pairs(pairs)
        
        result = f"""📊 **{title}** gerado com sucesso!

**Dados:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Gráfico interativo com hover, zoom e outras funcionalidades.*"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar gráfico de barras: {e}")
        return [TextContent(type="text", text=f"❌ Erro ao gerar gráfico de barras: {str(e)}")]


async def generate_line_chart(
    data: List[Dict[str, Union[str, float]]],
    title: str = "Gráfico de Linha",
    x_label: str = "X",
    y_label: str = "Y"
) -> List[TextContent]:
    """Gera um gráfico de linha interativo usando Plotly"""
    try:
        logger.info(f"📈 Gerando gráfico de linha: {title}")
        
        x_values = [item['category'] for item in data]
        y_values = [float(item['value']) for item in data]
        
        fig = go.Figure(data=[
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines+markers',
                hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>',
                line=dict(color='rgb(26, 118, 255)', width=3),
                marker=dict(color='rgb(26, 118, 255)', size=8)
            )
        ])
        
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            xaxis_title=x_label,
            yaxis_title=y_label,
            width=800,
            height=600,
            margin=dict(t=100, b=100, l=80, r=50),
            hovermode='x unified'
        )
        
        chart_data = _fig_to_json_data(fig)
        pairs = [(item['category'], item['value']) for item in data]
        summary = _format_pairs(pairs)
        
        result = f"""📈 **{title}** gerado com sucesso!

**Dados:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Gráfico de linha interativo com zoom, pan e hover.*"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar gráfico de linha: {e}")
        return [TextContent(type="text", text=f"❌ Erro ao gerar gráfico de linha: {str(e)}")]


async def generate_area_chart(
    data: List[Dict[str, Union[str, float]]],
    title: str = "Gráfico de Área",
    x_label: str = "X",
    y_label: str = "Y",
    fill_color: str = "rgba(26, 118, 255, 0.3)"
) -> List[TextContent]:
    """Gera um gráfico de área interativo usando Plotly"""
    try:
        logger.info(f"📈 Gerando gráfico de área: {title}")
        
        x_values = [item['category'] for item in data]
        y_values = [float(item['value']) for item in data]
        
        fig = go.Figure(data=[
            go.Scatter(
                x=x_values,
                y=y_values,
                mode='lines',
                fill='tonexty' if len(x_values) > 1 else 'tozeroy',
                fillcolor=fill_color,
                line=dict(color='rgb(26, 118, 255)', width=2),
                hovertemplate='<b>%{x}</b><br>%{y}<extra></extra>',
                name='Área'
            )
        ])
        
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            xaxis_title=x_label,
            yaxis_title=y_label,
            width=800,
            height=600,
            margin=dict(t=100, b=100, l=80, r=50),
            hovermode='x unified',
            showlegend=False
        )
        
        chart_data = _fig_to_json_data(fig)
        pairs = [(item['category'], item['value']) for item in data]
        summary = _format_pairs(pairs)
        
        result = f"""📈 **{title}** gerado com sucesso!

**Dados:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Gráfico de área interativo ideal para mostrar evolução e volume ao longo do tempo.*"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar gráfico de área: {e}")
        return [TextContent(type="text", text=f"❌ Erro ao gerar gráfico de área: {str(e)}")]


async def generate_column_chart(
    data: List[Dict[str, Union[str, float]]],
    title: str = "Gráfico de Colunas",
    x_label: str = "Categorias", 
    y_label: str = "Valores"
) -> List[TextContent]:
    """Gera um gráfico de colunas interativo usando Plotly (igual ao bar_chart mas semanticamente diferente)"""
    # Reutiliza a lógica do bar_chart
    return await generate_bar_chart(data, title, x_label, y_label)


async def generate_histogram(
    data: List[float],
    title: str = "Histograma",
    x_label: str = "Valores",
    y_label: str = "Frequência",
    nbins: int = 20
) -> List[TextContent]:
    """Gera um histograma interativo usando Plotly para análise de distribuição"""
    try:
        logger.info(f"📊 Gerando histograma: {title}")
        
        fig = go.Figure(data=[
            go.Histogram(
                x=data,
                nbinsx=nbins,
                hovertemplate='<b>Intervalo:</b> %{x}<br><b>Frequência:</b> %{y}<extra></extra>',
                marker_color='rgb(26, 118, 255)',
                marker_line_color='rgb(8, 48, 107)',
                marker_line_width=1.5,
                opacity=0.8
            )
        ])
        
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            xaxis_title=x_label,
            yaxis_title=y_label,
            width=800,
            height=600,
            margin=dict(t=100, b=100, l=80, r=50),
            bargap=0.1
        )
        
        chart_data = _fig_to_json_data(fig)
        
        # Estatísticas básicas
        import statistics
        mean_val = statistics.mean(data)
        median_val = statistics.median(data)
        std_val = statistics.stdev(data) if len(data) > 1 else 0
        
        summary = f"• Total de valores: {len(data)}\n• Média: {mean_val:.2f}\n• Mediana: {median_val:.2f}\n• Desvio padrão: {std_val:.2f}\n• Min: {min(data):.2f}\n• Max: {max(data):.2f}"
        
        result = f"""📊 **{title}** gerado com sucesso!

**Estatísticas:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Histograma interativo mostrando a distribuição dos valores com {nbins} bins.*"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar histograma: {e}")
        return [TextContent(type="text", text=f"❌ Erro ao gerar histograma: {str(e)}")]


async def generate_box_plot(
    data: List[Dict[str, Union[str, float]]],
    title: str = "Box Plot",
    x_label: str = "Categorias",
    y_label: str = "Valores"
) -> List[TextContent]:
    """Gera um box plot interativo usando Plotly para análise estatística"""
    try:
        logger.info(f"📦 Gerando box plot: {title}")
        
        # Agrupa dados por categoria
        categories = {}
        for item in data:
            category = item['category']
            value = float(item['value'])
            if category not in categories:
                categories[category] = []
            categories[category].append(value)
        
        fig = go.Figure()
        
        for category, values in categories.items():
            fig.add_trace(go.Box(
                y=values,
                name=category,
                hovertemplate=f'<b>{category}</b><br>Valor: %{{y}}<extra></extra>',
                marker_color='rgb(26, 118, 255)',
                line_color='rgb(8, 48, 107)',
                fillcolor='rgba(26, 118, 255, 0.3)'
            ))
        
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            xaxis_title=x_label,
            yaxis_title=y_label,
            width=800,
            height=600,
            margin=dict(t=100, b=100, l=80, r=50),
            showlegend=len(categories) > 1
        )
        
        chart_data = _fig_to_json_data(fig)
        
        # Estatísticas por categoria
        stats_summary = []
        for category, values in categories.items():
            import statistics
            mean_val = statistics.mean(values)
            median_val = statistics.median(values)
            q1 = statistics.quantiles(values, n=4)[0] if len(values) > 1 else values[0]
            q3 = statistics.quantiles(values, n=4)[2] if len(values) > 1 else values[0]
            stats_summary.append(f"• {category}: Mediana={median_val:.2f}, Q1={q1:.2f}, Q3={q3:.2f}, Média={mean_val:.2f}")
        
        summary = "\n".join(stats_summary)
        
        result = f"""📦 **{title}** gerado com sucesso!

**Estatísticas por Categoria:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Box plot interativo mostrando quartis, mediana, outliers e distribuição por categoria.*"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar box plot: {e}")
        return [TextContent(type="text", text=f"❌ Erro ao gerar box plot: {str(e)}")]


async def generate_distribution_plot(
    data: List[float],
    title: str = "Gráfico de Distribuição",
    x_label: str = "Valores",
    show_hist: bool = True,
    show_curve: bool = True
) -> List[TextContent]:
    """Gera um gráfico de distribuição (histograma + curva de densidade) usando Plotly"""
    try:
        logger.info(f"📈 Gerando gráfico de distribuição: {title}")
        
        fig = go.Figure()
        
        # Adiciona histograma se solicitado
        if show_hist:
            fig.add_trace(go.Histogram(
                x=data,
                histnorm='probability density',
                name='Histograma',
                marker_color='rgba(26, 118, 255, 0.6)',
                marker_line_color='rgb(8, 48, 107)',
                marker_line_width=1,
                hovertemplate='<b>Intervalo:</b> %{x}<br><b>Densidade:</b> %{y:.4f}<extra></extra>'
            ))
        
        # Adiciona curva de densidade se solicitado
        if show_curve:
            # Calcula densidade usando kernel density estimation simplificado
            import statistics
            import math
            
            # Ordena os dados
            sorted_data = sorted(data)
            n = len(data)
            
            # Calcula bandwidth usando regra de Scott
            std_dev = statistics.stdev(data) if n > 1 else 1
            bandwidth = 1.06 * std_dev * (n ** (-1/5))
            
            # Cria pontos para a curva
            min_val, max_val = min(data), max(data)
            range_val = max_val - min_val
            x_curve = [min_val - range_val * 0.1 + i * (range_val * 1.2) / 200 for i in range(201)]
            
            # Calcula densidade para cada ponto
            y_curve = []
            for x in x_curve:
                density = 0
                for point in data:
                    # Kernel gaussiano
                    u = (x - point) / bandwidth
                    kernel_val = (1 / math.sqrt(2 * math.pi)) * math.exp(-0.5 * u * u)
                    density += kernel_val
                density /= (n * bandwidth)
                y_curve.append(density)
            
            fig.add_trace(go.Scatter(
                x=x_curve,
                y=y_curve,
                mode='lines',
                name='Curva de Densidade',
                line=dict(color='rgb(255, 127, 14)', width=3),
                hovertemplate='<b>Valor:</b> %{x:.2f}<br><b>Densidade:</b> %{y:.4f}<extra></extra>'
            ))
        
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            xaxis_title=x_label,
            yaxis_title='Densidade de Probabilidade',
            width=800,
            height=600,
            margin=dict(t=100, b=100, l=80, r=50),
            showlegend=True,
            legend=dict(x=0.7, y=0.9)
        )
        
        chart_data = _fig_to_json_data(fig)
        
        # Estatísticas da distribuição
        import statistics
        mean_val = statistics.mean(data)
        median_val = statistics.median(data)
        std_val = statistics.stdev(data) if len(data) > 1 else 0
        
        # Calcula assimetria (skewness) simplificada
        if std_val > 0:
            skewness = sum(((x - mean_val) / std_val) ** 3 for x in data) / len(data)
        else:
            skewness = 0
        
        # Calcula curtose simplificada
        if std_val > 0:
            kurtosis = sum(((x - mean_val) / std_val) ** 4 for x in data) / len(data) - 3
        else:
            kurtosis = 0
        
        summary = f"""• Total de valores: {len(data)}
• Média: {mean_val:.3f}
• Mediana: {median_val:.3f}
• Desvio padrão: {std_val:.3f}
• Assimetria: {skewness:.3f}
• Curtose: {kurtosis:.3f}
• Min: {min(data):.3f}
• Max: {max(data):.3f}"""
        
        components = []
        if show_hist:
            components.append("histograma")
        if show_curve:
            components.append("curva de densidade")
        
        result = f"""📈 **{title}** gerado com sucesso!

**Estatísticas da Distribuição:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Gráfico de distribuição interativo com {' e '.join(components)} para análise estatística completa.*"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar gráfico de distribuição: {e}")
        return [TextContent(type="text", text=f"❌ Erro ao gerar gráfico de distribuição: {str(e)}")]


async def generate_scatter_plot(
    data: List[Dict[str, Union[float, str]]],
    title: str = "Gráfico de Dispersão",
    x_label: str = "Eixo X",
    y_label: str = "Eixo Y",
    color_by_category: bool = False,
    show_trendline: bool = False,
    point_size: int = 8
) -> List[TextContent]:
    """Gera um gráfico de dispersão interativo usando Plotly para análise de correlação"""
    try:
        logger.info(f"🔍 Gerando gráfico de dispersão: {title}")
        
        # Extrai coordenadas x e y
        x_values = [float(item['x']) for item in data]
        y_values = [float(item['y']) for item in data]
        
        fig = go.Figure()
        
        # Se colorir por categoria e há categorias nos dados
        if color_by_category and any('category' in item for item in data):
            # Agrupa por categoria
            categories = {}
            for item in data:
                category = item.get('category', 'Sem Categoria')
                if category not in categories:
                    categories[category] = {'x': [], 'y': []}
                categories[category]['x'].append(float(item['x']))
                categories[category]['y'].append(float(item['y']))
            
            # Cores para diferentes categorias
            colors = ['rgb(26, 118, 255)', 'rgb(255, 127, 14)', 'rgb(44, 160, 44)', 
                     'rgb(214, 39, 40)', 'rgb(148, 103, 189)', 'rgb(140, 86, 75)',
                     'rgb(227, 119, 194)', 'rgb(127, 127, 127)', 'rgb(188, 189, 34)', 'rgb(23, 190, 207)']
            
            for i, (category, values) in enumerate(categories.items()):
                color = colors[i % len(colors)]
                fig.add_trace(go.Scatter(
                    x=values['x'],
                    y=values['y'],
                    mode='markers',
                    name=category,
                    marker=dict(
                        size=point_size,
                        color=color,
                        opacity=0.7,
                        line=dict(width=1, color='white')
                    ),
                    hovertemplate=f'<b>{category}</b><br>{x_label}: %{{x}}<br>{y_label}: %{{y}}<extra></extra>'
                ))
        else:
            # Gráfico simples sem categorias
            fig.add_trace(go.Scatter(
                x=x_values,
                y=y_values,
                mode='markers',
                name='Pontos',
                marker=dict(
                    size=point_size,
                    color='rgb(26, 118, 255)',
                    opacity=0.7,
                    line=dict(width=1, color='white')
                ),
                hovertemplate=f'<b>Ponto</b><br>{x_label}: %{{x}}<br>{y_label}: %{{y}}<extra></extra>'
            ))
        
        # Adiciona linha de tendência se solicitado
        if show_trendline and len(x_values) > 1:
            # Calcula regressão linear simples
            import statistics
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x * x for x in x_values)
            
            # Coeficientes da regressão linear (y = ax + b)
            if n * sum_x2 - sum_x * sum_x != 0:
                a = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
                b = (sum_y - a * sum_x) / n
                
                # Pontos da linha de tendência
                x_min, x_max = min(x_values), max(x_values)
                x_trend = [x_min, x_max]
                y_trend = [a * x + b for x in x_trend]
                
                fig.add_trace(go.Scatter(
                    x=x_trend,
                    y=y_trend,
                    mode='lines',
                    name='Linha de Tendência',
                    line=dict(color='red', width=2, dash='dash'),
                    hovertemplate=f'<b>Tendência</b><br>y = {a:.3f}x + {b:.3f}<extra></extra>'
                ))
        
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            xaxis_title=x_label,
            yaxis_title=y_label,
            width=800,
            height=600,
            margin=dict(t=100, b=100, l=80, r=50),
            showlegend=color_by_category or show_trendline,
            hovermode='closest'
        )
        
        chart_data = _fig_to_json_data(fig)
        
        # Calcula estatísticas de correlação
        import statistics
        if len(x_values) > 1:
            # Coeficiente de correlação de Pearson
            mean_x = statistics.mean(x_values)
            mean_y = statistics.mean(y_values)
            
            numerator = sum((x - mean_x) * (y - mean_y) for x, y in zip(x_values, y_values))
            sum_sq_x = sum((x - mean_x) ** 2 for x in x_values)
            sum_sq_y = sum((y - mean_y) ** 2 for y in y_values)
            
            if sum_sq_x > 0 and sum_sq_y > 0:
                correlation = numerator / (sum_sq_x * sum_sq_y) ** 0.5
            else:
                correlation = 0
        else:
            correlation = 0
        
        # Estatísticas descritivas
        stats_x = {
            'min': min(x_values) if x_values else 0,
            'max': max(x_values) if x_values else 0,
            'mean': statistics.mean(x_values) if x_values else 0
        }
        
        stats_y = {
            'min': min(y_values) if y_values else 0,
            'max': max(y_values) if y_values else 0,
            'mean': statistics.mean(y_values) if y_values else 0
        }
        
        summary = f"""• Total de pontos: {len(data)}
• Correlação (Pearson): {correlation:.3f}
• {x_label} - Min: {stats_x['min']:.2f}, Max: {stats_x['max']:.2f}, Média: {stats_x['mean']:.2f}
• {y_label} - Min: {stats_y['min']:.2f}, Max: {stats_y['max']:.2f}, Média: {stats_y['mean']:.2f}"""
        
        features = []
        if color_by_category and any('category' in item for item in data):
            features.append("colorido por categoria")
        if show_trendline:
            features.append("linha de tendência")
        
        features_text = f" com {' e '.join(features)}" if features else ""
        
        result = f"""🔍 **{title}** gerado com sucesso!

**Estatísticas de Correlação:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Gráfico de dispersão interativo{features_text} para análise de correlação entre variáveis.*"""
        
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar gráfico de dispersão: {e}")
        return [TextContent(type="text", text=f"❌ Erro ao gerar gráfico de dispersão: {str(e)}")]


async def generate_heatmap(
    z_data: List[List[float]],
    x_labels: Optional[List[str]] = None,
    y_labels: Optional[List[str]] = None,
    title: str = "Heatmap",
    x_label: str = "X",
    y_label: str = "Y",
    colorscale: str = "Viridis",
    show_values: bool = True,
    colorbar_title: str = "Valor"
) -> List[TextContent]:
    """
    Gera um heatmap (mapa de calor) interativo usando Plotly.
    Baseado em: https://plotly.com/python/heatmaps/
    
    Args:
        z_data: Matriz 2D de valores (lista de listas)
        x_labels: Labels para o eixo X (opcional)
        y_labels: Labels para o eixo Y (opcional)
        title: Título do gráfico
        x_label: Label do eixo X
        y_label: Label do eixo Y
        colorscale: Escala de cores (Viridis, RdBu, Blues, Reds, etc.)
        show_values: Mostrar valores nas células
        colorbar_title: Título da barra de cores
    
    Returns:
        Lista com TextContent contendo o gráfico em formato JSON
    """
    try:
        logger.info(f"📊 Gerando heatmap: {title}")
        
        if not z_data or not isinstance(z_data, list):
            raise ValueError("z_data deve ser uma lista de listas (matriz 2D)")
        
        # Cria o heatmap
        fig = go.Figure(data=go.Heatmap(
            z=z_data,
            x=x_labels if x_labels else None,
            y=y_labels if y_labels else None,
            colorscale=colorscale,
            text=z_data if show_values else None,
            texttemplate="%{text:.2f}" if show_values else None,
            textfont={"size": 10},
            colorbar=dict(
                title=colorbar_title,
                titleside="right",
                tickmode="linear",
                tick0=0,
                dtick=1
            ),
            hoverongaps=False,
            hovertemplate='<b>%{y}</b> × <b>%{x}</b><br>Valor: %{z:.3f}<extra></extra>'
        ))
        
        # Configurações do layout
        fig.update_layout(
            title={'text': title, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 18}},
            xaxis_title=x_label,
            yaxis_title=y_label,
            width=800,
            height=600,
            margin=dict(t=100, b=100, l=120, r=120),
            xaxis=dict(
                side='bottom',
                tickangle=-45 if x_labels and len(x_labels) > 5 else 0
            ),
            yaxis=dict(
                autorange='reversed' if not y_labels else True
            )
        )
        
        chart_data = _fig_to_json_data(fig)
        
        # Calcula estatísticas da matriz
        import statistics
        flat_values = [val for row in z_data for val in row if val is not None]
        
        if flat_values:
            min_val = min(flat_values)
            max_val = max(flat_values)
            mean_val = statistics.mean(flat_values)
            median_val = statistics.median(flat_values)
            
            summary = f"""• Dimensões: {len(z_data)} × {len(z_data[0]) if z_data else 0}
• Valores: {len(flat_values)} células
• Mínimo: {min_val:.3f}
• Máximo: {max_val:.3f}
• Média: {mean_val:.3f}
• Mediana: {median_val:.3f}"""
        else:
            summary = "Sem dados válidos para estatísticas"
        
        result = f"""🔥 **{title}** gerado com sucesso!

**Estatísticas da Matriz:**
{summary}

**PLOTLY_CHART_DATA:**
{json.dumps(chart_data)}

*Heatmap interativo com escala de cores {colorscale} para visualização de padrões e correlações em dados bidimensionais.*"""
        
        logger.info(f"✅ Heatmap gerado com sucesso: {title}")
        return [TextContent(type="text", text=result)]
        
    except Exception as e:
        logger.error(f"❌ Erro ao gerar heatmap: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return [TextContent(type="text", text=f"❌ Erro ao gerar heatmap: {str(e)}")]


async def main():
    """Função principal para executar o servidor MCP"""
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
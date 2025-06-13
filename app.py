import streamlit as st
import pandas as pd
import environ
from dados_receita import autenticar_msal, baixar_arquivo, carregar_planilha, processar_arquivos
from utils_receita import filtrar_dados, calcular_metricas, padronizar_e_limpar
import plotly_express as px

env = environ.Env()
environ.Env().read_env()

drive_id = env("drive_id")

arquivos = [
    {"nome": "Recebimentos_Caixa.xlsx", "caminho": "/Recebimentos%20Caixa%20(1).xlsx", "aba": "ENTRADAS", "linhas_pular": 4},
    {"nome": "P._conta_2025.xlsx", "caminho": "/P.conta%202025.xlsx", "aba": "Prestação", "linhas_pular": 5},
    {"nome": "Venda_Balcao.xlsx", "caminho": "/Venda%20Balc%C3%A3o.xlsx", "aba": None, "linhas_pular": 0} 
]

token = autenticar_msal()
headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

df = processar_arquivos(arquivos, drive_id, headers)
df_balcao = df[df['ORIGEM'] == 'Venda_Balcao']

df = padronizar_e_limpar(df)

st.set_page_config(layout="centered", page_title="Análise de Receitas", page_icon="📊")
st.title("Dashboard de Análise Financeira")

opcoes_periodo = ["Semana Atual", "Semana Passada", "Mês Atual", "Mês Passado", "Últimos 3 Meses", "Últimos 6 Meses", "Ano Atual", "Ano Passado", "Tempo Todo"]
periodo_selecionado = st.selectbox("Selecione o Período:", opcoes_periodo)

df_filtrado, inicio_periodo, fim_periodo = filtrar_dados(df, periodo_selecionado)

if inicio_periodo and fim_periodo:
    st.write(f"**Início do Período:** {inicio_periodo.strftime('%d/%m/%Y')}")
    st.write(f"**Fim do Período:** {fim_periodo.strftime('%d/%m/%Y')}")

st.markdown("## Métricas de Receitas")
vendas_total, receita_media, quantidade_transacoes = calcular_metricas(df_filtrado)
col1, col2, col3 = st.columns(3)

col1.metric("Total de Vendas", f"R$ {vendas_total:,.2f}", delta_color="inverse")
col2.metric("Número de Transações", quantidade_transacoes)
col3.metric("Valor Médio por Transação", f"R$ {receita_media:,.2f}")

df_balcao_filtrado, _, _ = filtrar_dados(df_balcao, periodo_selecionado)

# 📊 Calcular métricas para Vendas Balcão
receita_balcao_total = df_balcao_filtrado['VALOR R$'].sum()
receita_balcao_media = df_balcao_filtrado['VALOR R$'].mean() if not df_balcao_filtrado.empty else 0
quantidade_balcao_transacoes = len(df_balcao_filtrado)

# 📊 Exibir Métricas de Vendas Balcão SOMENTE SE houver vendas
if receita_balcao_total > 0 or quantidade_balcao_transacoes > 0 or receita_balcao_media > 0:
    st.markdown("## Métricas de Vendas Balcão")
    col_balcao1, col_balcao2, col_balcao3 = st.columns(3)
    col_balcao1.metric("Total de Vendas Balcão", f"R$ {receita_balcao_total:,.2f}", delta_color="inverse")
    col_balcao2.metric("Número de Transações Balcão", quantidade_balcao_transacoes)
    col_balcao3.metric("Valor Médio por Transação Balcão", f"R$ {receita_balcao_media:,.2f}")

# 🔸 Cálculo das métricas líquidas (excluindo Vendas Balcão)
receita_liquida = vendas_total - receita_balcao_total
transacoes_liquidas = quantidade_transacoes - quantidade_balcao_transacoes
ticket_medio_liquido = receita_liquida / transacoes_liquidas if transacoes_liquidas > 0 else 0

opcoes_graficos = [
    "Ticket Médio por Técnico",
    "Receita Total por Técnico",
    "Receita Mão de Obra por Técnico",
    "Receita de Peças por Técnico"
]

grafico_selecionado = st.radio("Escolha um gráfico para visualizar:", opcoes_graficos)  

ticket_medio = df_filtrado.groupby('TÉCNICO')['VALOR R$'].mean().reset_index()
ticket_medio.rename(columns={'VALOR R$': 'ticket médio'}, inplace=True)
ticket_medio = ticket_medio.sort_values(by='ticket médio', ascending=False)

receita_total = df_filtrado.groupby('TÉCNICO')['VALOR R$'].sum().reset_index()
receita_total.rename(columns={'VALOR R$': 'receita total'}, inplace=True)
receita_total = receita_total.sort_values(by='receita total', ascending=False)

df_filtrado['M.O'] = pd.to_numeric(df_filtrado['M.O'], errors='coerce').fillna(0)
receita_mao_de_obra = df_filtrado.groupby('TÉCNICO')['M.O'].sum().reset_index()
receita_mao_de_obra.rename(columns={'M.O': 'receita mão de obra'}, inplace=True)
receita_mao_de_obra = receita_mao_de_obra.sort_values(by='receita mão de obra', ascending=False)

df_filtrado['PEÇAS'] = pd.to_numeric(df_filtrado['PEÇAS'], errors='coerce').fillna(0)
receita_pecas = df_filtrado.groupby('TÉCNICO')['PEÇAS'].sum().reset_index()
receita_pecas.rename(columns={'PEÇAS': 'receita peças'}, inplace=True)
receita_pecas = receita_pecas.sort_values(by='receita peças', ascending=False)

if grafico_selecionado == "Ticket Médio por Técnico":
    ticket_medio = ticket_medio[ticket_medio['TÉCNICO'] != 'NÃO INFORMADO']
    st.subheader("Ticket Médio por Técnico")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(ticket_medio)
    with col2:
        fig_ticket_medio = px.bar(ticket_medio, x='TÉCNICO', y='ticket médio', title="Ticket Médio por Técnico", color='TÉCNICO')
        st.plotly_chart(fig_ticket_medio, use_container_width=True)

elif grafico_selecionado == "Receita Total por Técnico":
    receita_total = receita_total[receita_total['TÉCNICO'] != 'NÃO INFORMADO']
    st.subheader("Receita Total por Técnico")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(receita_total)
    with col2:
        fig_receita_total = px.pie(receita_total, names='TÉCNICO', values='receita total', title="Receita Total por Técnico")
        st.plotly_chart(fig_receita_total, use_container_width=True)

elif grafico_selecionado == "Receita Mão de Obra por Técnico":
    receita_mao_de_obra = receita_mao_de_obra[receita_mao_de_obra['TÉCNICO'] != 'NÃO INFORMADO']
    st.subheader("Receita Mão de Obra por Técnico")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(receita_mao_de_obra)
    with col2:
        fig_receita_mao_de_obra = px.pie(receita_mao_de_obra, names='TÉCNICO', values='receita mão de obra', title="Receita Mão de Obra por Técnico")
        st.plotly_chart(fig_receita_mao_de_obra, use_container_width=True)

elif grafico_selecionado == "Receita de Peças por Técnico":
    receita_pecas = receita_pecas[receita_pecas['TÉCNICO'] != 'NÃO INFORMADO']
    st.subheader("Receita de Peças por Técnico")
    col1, col2 = st.columns(2)
    with col1:
        st.dataframe(receita_pecas)
    with col2:
        fig_receita_pecas = px.pie(receita_pecas, names='TÉCNICO', values='receita peças', title="Receita de Peças por Técnico")
        st.plotly_chart(fig_receita_pecas, use_container_width=True)

import json
import requests
from msal import ConfidentialClientApplication
import streamlit as st
import pandas as pd
from unidecode import unidecode
import plotly.express as px
from datetime import datetime, timedelta
from io import BytesIO
import environ
from calendar import monthrange 
# Autenticação e download dos arquivos
env = environ.Env()
environ.Env().read_env()

client_id = env("id_do_cliente")
client_secret = env("segredo")
tenant_id = env("tenant_id")
msal_authority = f"https://login.microsoftonline.com/{tenant_id}"
msal_scope = ["https://graph.microsoft.com/.default"]

# Configurando a aplicação MSAL
msal_app = ConfidentialClientApplication(
    client_id=client_id,
    client_credential=client_secret,
    authority=msal_authority,
)

# Tentando adquirir o token
result = msal_app.acquire_token_silent(scopes=msal_scope, account=None)
if not result:
    result = msal_app.acquire_token_for_client(scopes=msal_scope)

# Verifica se o token foi adquirido com sucesso
if "access_token" in result:
    access_token = result["access_token"]
else:
    raise Exception("No Access Token found")

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}

# Usando o ID da biblioteca de documentos correta
drive_id = env("drive_id")
file_paths = {
    "PLANILHA_DE_CUSTO.xlsx": "/PLANILHA%20DE%20CUSTO%202024%20(2).xlsx",
    "Recebimentos_Caixa.xlsx": "/Recebimentos%20Caixa%20(1).xlsx"
}

def download_file(file_name, file_path):
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:{file_path}:/content"
    response = requests.get(url=url, headers=headers)
    if response.status_code == 200:
        with open(file_name, "wb") as f:
            f.write(response.content)
        print(f"{file_name} baixado com sucesso!")
    else:
        print(f"Erro ao acessar {file_name}: {response.status_code}, {response.text}")

for file_name, path in file_paths.items():
    download_file(file_name, path)

# Carregar as planilhas específicas "LANÇAMENTO DESPESAS"
planilha_1 = pd.read_excel('Recebimentos_Caixa.xlsx', sheet_name='LANÇAMENTO DESPESAS', skiprows=3)
planilha_2 = pd.read_excel('PLANILHA_DE_CUSTO.xlsx', sheet_name='LANÇAMENTO DESPESAS', skiprows=3)

# Ajustar as colunas dinamicamente
colunas = ['Data', 'Grupo Despesas', 'Tipo Despesas', 'Usuário', 'Descrição Despesa', 'Valor R$', 'Observação',
           'Coluna8', 'Coluna9', 'Coluna10', 'Coluna11', 'Coluna12', 'Mês', 'Coluna Extra']
if len(planilha_1.columns) == 14:
    planilha_1.columns = colunas
if len(planilha_2.columns) == 14:
    planilha_2.columns = colunas

# Remover colunas extras 
colunas_a_remover = ['Coluna8', 'Coluna9', 'Coluna10', 'Coluna11', 'Coluna12', 'Mês', 'Coluna Extra']
planilha_1 = planilha_1.drop(columns=colunas_a_remover, errors='ignore')
planilha_2 = planilha_2.drop(columns=colunas_a_remover, errors='ignore')

# Concatenar as planilhas em uma única tabela
planilhas_combinadas = pd.concat([planilha_1, planilha_2], ignore_index=True)

# Funções de soma e média
def soma_por_grupo_despesa(planilha):
    # Garantir que 'Valor R$' é numérico
    planilha['Valor R$'] = pd.to_numeric(planilha['Valor R$'], errors='coerce')
    return planilha.groupby('Grupo Despesas')['Valor R$'].sum().reset_index()

# Padronizar nomes de usuários
def padronizar_nome_usuario(planilha):
    planilha['Usuário'] = planilha['Usuário'].apply(lambda x: unidecode(str(x)).upper())
    return planilha

planilhas_combinadas = padronizar_nome_usuario(planilhas_combinadas)

# Listar colunas de texto para preencher NaNs com "Não informado"
colunas_texto = ['Grupo Despesas', 'Tipo Despesas', 'Usuário', 'Descrição Despesa', 'Observação']

# Preencher NaNs nas colunas de texto
planilhas_combinadas[colunas_texto] = planilhas_combinadas[colunas_texto].fillna("Não informado")

# Certificar-se de que 'Valor R$' é numérico
planilhas_combinadas['Valor R$'] = pd.to_numeric(planilhas_combinadas['Valor R$'], errors='coerce')

# Remover apenas linhas completamente vazias
planilhas_combinadas = planilhas_combinadas.dropna(how='all')

# Convertendo a coluna de data para tipo datetime e removendo NaN
planilhas_combinadas['Data'] = pd.to_datetime(planilhas_combinadas['Data'], errors='coerce')
planilhas_combinadas.dropna(subset=['Data', 'Grupo Despesas', 'Tipo Despesas', 'Usuário', 'Valor R$'], inplace=True)
planilhas_combinadas['Data'] = planilhas_combinadas['Data'].dt.strftime('%d/%m/%Y')


# Configurar o layout do dashboard
st.set_page_config(layout="wide", page_title="Análise de Despesas", page_icon="📊")

# Estilos e título do dashboard
st.markdown(
    """
    <style>
    .main-title { font-size: 42px; font-weight: bold; color: #FFFAFA; text-align: center; margin-bottom: 20px; }
    .table-title { font-size: 30px; font-weight: bold; color: #F8F8FF; text-align: center; margin-top: 20px; margin-bottom: 20px; }
    </style>
    """,
    unsafe_allow_html=True
)
st.markdown('<div class="main-title">Análise Financeira de Despesas</div>', unsafe_allow_html=True)

# Barra lateral para filtros
st.sidebar.title("Filtros")
st.sidebar.subheader("Filtrar por Período")
opcoes_periodo = [
    "Mês atual", "Mês passado", "Últimos 30 dias", "Semana atual", "Semana passada",
    "Últimos 3 meses até agora", "Ano atual", "Ano passado", "Hoje", "Tempo todo (Interno)"
]
periodo_selecionado = st.sidebar.selectbox("Selecione o período:", opcoes_periodo)

# Lógica para intervalo de datas
data_mais_recente = planilhas_combinadas['Data'].max()
data_inicio = {
    "Mês atual": datetime(data_mais_recente.year, data_mais_recente.month, 1),
    "Mês passado": None,
    "Últimos 30 dias": data_mais_recente - timedelta(days=30),
    "Semana atual": data_mais_recente - timedelta(days=data_mais_recente.weekday()),
    "Semana passada": None,
    "Últimos 3 meses até agora": data_mais_recente - timedelta(days=90),
    "Ano atual": datetime(data_mais_recente.year, 1, 1),
    "Ano passado": datetime(data_mais_recente.year - 1, 1, 1),
    "Hoje": data_mais_recente,
    "Tempo todo (Interno)": planilhas_combinadas['Data'].min()
}

# Ajustar a data final para o mês passado
if periodo_selecionado == "Mês passado":
    ano_mes_passado = data_mais_recente.year if data_mais_recente.month > 1 else data_mais_recente.year - 1
    mes_mes_passado = data_mais_recente.month - 1 if data_mais_recente.month > 1 else 12
    ultimo_dia_mes_passado = monthrange(ano_mes_passado, mes_mes_passado)[1]
    
    data_inicio["Mês passado"] = datetime(ano_mes_passado, mes_mes_passado, 1)
    data_mais_recente = datetime(ano_mes_passado, mes_mes_passado, ultimo_dia_mes_passado)

    # Ajustar a data de início e fim para "Semana passada"
if periodo_selecionado == "Semana passada":
    inicio_semana_atual = data_mais_recente - timedelta(days=data_mais_recente.weekday())
    fim_semana_passada = inicio_semana_atual - timedelta(days=1)
    inicio_semana_passada = fim_semana_passada - timedelta(days=6)
    
    data_inicio["Semana passada"] = inicio_semana_passada
    data_mais_recente = fim_semana_passada

# Aplicar o filtro de datas
filtro_data = planilhas_combinadas[
    (planilhas_combinadas['Data'] >= data_inicio[periodo_selecionado]) &
    (planilhas_combinadas['Data'] <= data_mais_recente)
]
# Ordenar os dados filtrados por data de forma decrescente
filtro_data = filtro_data.sort_values(by='Data', ascending=False)

# Filtro por Grupo Despesas
if 'grupo_despesas' not in st.session_state:
    st.session_state['grupo_despesas'] = []

grupos_despesas = st.sidebar.multiselect(
    'Selecione o(s) Grupo(s) de Despesas:',
    options=filtro_data['Grupo Despesas'].unique(),
    default=st.session_state['grupo_despesas']
)

st.session_state['grupo_despesas'] = grupos_despesas

# Aplicar filtro se houver seleção
if grupos_despesas:
    filtro_grupo = filtro_data[filtro_data['Grupo Despesas'].isin(grupos_despesas)]
else:
    filtro_grupo = filtro_data

# Filtro por Tipo de Despesas
if 'tipo_despesas' not in st.session_state:
    st.session_state['tipo_despesas'] = []

tipos_despesas = st.sidebar.multiselect(
    'Selecione o(s) Tipo(s) de Despesa:',
    options=filtro_grupo['Tipo Despesas'].unique(),
    default=st.session_state['tipo_despesas']
)

st.session_state['tipo_despesas'] = tipos_despesas

# Aplicar filtro se houver seleção
if tipos_despesas:
    filtro_tipo = filtro_grupo[filtro_grupo['Tipo Despesas'].isin(tipos_despesas)]
else:
    filtro_tipo = filtro_grupo

# Filtro por Usuário
if 'usuarios' not in st.session_state:
    st.session_state['usuarios'] = []

usuarios = st.sidebar.multiselect(
    'Selecione o(s) Usuário(s):',
    options=filtro_tipo['Usuário'].unique(),
    default=st.session_state['usuarios']
)

st.session_state['usuarios'] = usuarios

# Aplicar filtro se houver seleção
if usuarios:
    filtro_usuario = filtro_tipo[filtro_tipo['Usuário'].isin(usuarios)]
else:
    filtro_usuario = filtro_tipo

# Filtro por Intervalo de Valores
valor_min, valor_max = st.sidebar.slider(
    'Selecione o intervalo de valores (R$):',
    min_value=0,
    max_value=int(filtro_usuario['Valor R$'].max()),
    value=(0, int(filtro_usuario['Valor R$'].max()))
)

filtro_final = filtro_usuario[(filtro_usuario['Valor R$'] >= valor_min) & (filtro_usuario['Valor R$'] <= valor_max)]

# Remover o índice da tabela, formatar a coluna de data e substituir valores vazios
filtro_final_formatado = filtro_final.copy()
filtro_final_formatado['Data'] = filtro_final_formatado['Data'].dt.strftime('%d-%m-%Y')  # Formatar data como "24-10-2024"

# Substituir valores vazios por um valor mais amigável (ex: "Não informado")
filtro_final_formatado.fillna("Não informado", inplace=True)

# Exibir a tabela sem o índice
st.markdown('<div class="table-title">Dados Filtrados</div>', unsafe_allow_html=True)
st.dataframe(filtro_final_formatado.rename(columns={"Usuário Padronizado": "Usuário"}).reset_index(drop=True).style.format({"Valor R$": "R${:,.2f}"}), use_container_width=True)

# Divisão em colunas para exibir métricas principais
st.markdown("## Métricas de Despesas")
col1, col2, col3 = st.columns(3)
total_despesas = filtro_final['Valor R$'].sum()
num_transacoes = len(filtro_final)
valor_medio = filtro_final['Valor R$'].mean()

col1.metric("Total de Despesas", f"R$ {total_despesas:,.2f}", delta_color="inverse")
col2.metric("Número de Transações", num_transacoes)
col3.metric("Valor Médio por Transação", f"R$ {valor_medio:,.2f}")

@st.cache_data
def convert_df(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    processed_data = output.getvalue()
    return processed_data

excel_data = convert_df(filtro_final_formatado)

st.download_button(
    label="📥 Baixar dados filtrados",
    data=excel_data,
    file_name='dados_filtrados.xlsx',
    mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
)

# Gráfico de despesas por usuário padronizado
st.markdown("## Gráfico de Despesas por Usuário")
despesas_por_usuario = filtro_final.groupby('Usuário')['Valor R$'].sum().reset_index()
fig1 = px.bar(despesas_por_usuario, x='Usuário', y='Valor R$', title='Despesas por Usuário', 
              color='Usuário', color_continuous_scale=px.colors.sequential.Blues, template="plotly_white")
st.plotly_chart(fig1, use_container_width=True)

# Soma por grupo de despesa usando o DataFrame filtrado
soma_grupo = soma_por_grupo_despesa(filtro_final)

if not soma_grupo.empty:
    st.header("Gráfico de soma de despesas por grupo de despesa")
    fig = px.pie(soma_grupo, values='Valor R$', names='Grupo Despesas', title='Soma de despesas por grupo de despesa')
    st.plotly_chart(fig)
else:
    st.write("Nenhum dado disponível para gerar o gráfico com base nos filtros selecionados.")

if st.checkbox("Mostrar detalhes por Tipo de Despesa"):
    despesas_tipo = filtro_final.groupby('Tipo Despesas')['Valor R$'].sum().reset_index()
    fig3 = px.bar(despesas_tipo, x='Tipo Despesas', y='Valor R$', title='Despesas por Tipo')
    st.plotly_chart(fig3, use_container_width=True)
    

import pandas as pd
from datetime import datetime, timedelta
from unidecode import unidecode
from dateutil.relativedelta import relativedelta

def padronizar_nome(nome):
    if pd.isnull(nome):
        return "NÃO INFORMADO"
    nome = str(nome).upper()
    nome = unidecode(nome)
    nome = nome.strip()
    nome = ' '.join(nome.split())  # Remove espaços duplicados
    return nome

def padronizar_e_limpar(df):
    # Padroniza campos de texto
    for col in ["TIPO RECEITA", "USUÁRIO", "DESCRIÇÃO RECEITA"]:
        if col in df.columns:
            df[col] = df[col].fillna("Não informado")
    # Padroniza USUÁRIO para maiúsculas e sem acento
    if "USUÁRIO" in df.columns:
        df["USUÁRIO"] = df["USUÁRIO"].apply(padronizar_nome)
    # **Padronize também TÉCNICO!**
    if "TÉCNICO" in df.columns:
        df["TÉCNICO"] = df["TÉCNICO"].apply(padronizar_nome)
    # Garante que o valor está como float numérico
    if "VALOR R$" in df.columns:
        df["VALOR R$"] = pd.to_numeric(df["VALOR R$"], errors="coerce")
        df = df[df["VALOR R$"] > 0]
    if "DATA" in df.columns:
        df["DATA"] = pd.to_datetime(df["DATA"], errors="coerce")
    obrigatorios = [col for col in ["DATA", "TIPO RECEITA", "USUÁRIO", "VALOR R$"] if col in df.columns]
    df = df.dropna(subset=obrigatorios)
    return df

def filtrar_dados(df, periodo):
    hoje = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
    df = df.copy()
    data_inicio = None
    data_fim = None

    if periodo == "Semana Atual":
        data_inicio = hoje - timedelta(days=hoje.weekday())
        data_fim = hoje
    elif periodo == "Semana Passada":
        data_inicio = hoje - timedelta(days=hoje.weekday() + 7)
        data_fim = data_inicio + timedelta(days=6)
    elif periodo == "Mês Atual":
        data_inicio = hoje.replace(day=1)
        data_fim = hoje
    elif periodo == "Mês Passado":
        primeiro_dia_mes_passado = (hoje.replace(day=1) - timedelta(days=1)).replace(day=1)
        ultimo_dia_mes_passado = hoje.replace(day=1) - timedelta(days=1)
        data_inicio = primeiro_dia_mes_passado
        data_fim = ultimo_dia_mes_passado
    elif periodo == "Últimos 3 Meses":
        data_inicio = (hoje - relativedelta(months=3)).replace(day=1)
        data_fim = hoje
    elif periodo == "Últimos 6 Meses":
        data_inicio = (hoje - relativedelta(months=6)).replace(day=1)
        data_fim = hoje
    elif periodo == "Ano Atual":
        data_inicio = hoje.replace(month=1, day=1)
        data_fim = hoje
    elif periodo == "Ano Passado":
        data_inicio = hoje.replace(year=hoje.year - 1, month=1, day=1)
        data_fim = hoje.replace(year=hoje.year - 1, month=12, day=31)
    elif periodo == "Tempo Todo":
        return df, None, None
    else:
        return df, None, None
    
    if data_inicio and data_fim:
        df_filtrado = df[(df["DATA"] >= data_inicio) & (df["DATA"] <= data_fim)]
        return df_filtrado, data_inicio, data_fim
    else:
        return df, None, None

def calcular_metricas(df_filtrado):
    vendas_total = df_filtrado['VALOR R$'].sum()
    receita_media = df_filtrado['VALOR R$'].mean() if not df_filtrado.empty else 0
    quantidade_transacoes = len(df_filtrado)
    return vendas_total, receita_media, quantidade_transacoes
 
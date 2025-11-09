import pandas as pd
from django.shortcuts import render, redirect
from .forms import UploadExcelForm
import json


def upload_file(request):
    """Página inicial — upload do Excel"""
    form = UploadExcelForm()
    return render(request, 'upload.html', {'form': form})


def visualize(request):
    """Recebe o Excel, processa automaticamente e gera visualizações genéricas (com nomes de cidades, estados ou regiões)."""
    if request.method != 'POST' or 'excel_file' not in request.FILES:
        return redirect('alfadata:upload')

    excel_file = request.FILES['excel_file']

    # --- 🧾 Leitura segura do Excel ---
    try:
        df = pd.read_excel(excel_file)
    except Exception as e:
        return render(request, 'upload.html', {
            'form': UploadExcelForm(),
            'error': f'Erro ao ler Excel: {e}'
        })

    if df.empty:
        return render(request, 'upload.html', {
            'form': UploadExcelForm(),
            'error': 'Arquivo vazio ou inválido.'
        })

    # --- 🧹 Limpeza de dados ---
    df = df.applymap(
        lambda x: str(x).replace(',', '.').replace('> ', '')
        .replace('>', '').replace('-', '').strip()
        if isinstance(x, str) else x
    )

    # --- 🔍 Detectar automaticamente a coluna de cidade / estado / região ---
    possible_label_cols = []
    for col in df.columns:
        if df[col].dtype == 'object' and df[col].nunique() > 3 and df[col].nunique() < len(df):
            possible_label_cols.append(col)

    # Preferência para colunas com nome típico
    preferred_names = ['CIDADE', 'CIDADES', 'MUNICIPIO', 'MUNICÍPIO', 'ESTADO', 'UF', 'SIGLA_UF', 'NOME_UF', 'REGIÃO', 'REGIAO']
    label_col = None
    for name in preferred_names:
        for col in df.columns:
            if name.lower() in col.lower():
                label_col = col
                break
        if label_col:
            break

    # Se não encontrar nenhuma das preferidas, usa a primeira detectada
    if not label_col and possible_label_cols:
        label_col = possible_label_cols[0]

    # --- 🏷️ Eixo X ---
    if label_col:
        x_labels = df[label_col].astype(str).tolist()
    else:
        x_labels = df.index.astype(str).tolist()

    # --- 🔢 Conversão e detecção de colunas numéricas ---
    numeric_df = pd.DataFrame()
    for col in df.columns:
        if col == label_col:
            continue
        try:
            converted = pd.to_numeric(df[col], errors='coerce')
            if converted.notnull().mean() > 0.4:  # aceita colunas com mais de 40% de dados válidos
                numeric_df[col] = converted
        except Exception:
            continue

    # Verifica se há números
    if numeric_df.empty:
        return render(request, 'upload.html', {
            'form': UploadExcelForm(),
            'error': 'Nenhuma coluna numérica encontrada (verifique formato dos valores).'
        })

    # Limita para não travar gráficos
    if len(numeric_df) > 2000:
        numeric_df = numeric_df.head(2000)

    # --- 🎨 Cria datasets para os gráficos ---
    datasets = []
    for col in numeric_df.columns:
        datasets.append({
            'label': str(col),
            'data': numeric_df[col].fillna(0).tolist(),
            'fill': False,
        })

    chart_data = {
        'labels': x_labels,
        'datasets': datasets
    }

    # --- 💡 Geração de insights automáticos ---
    insights = []
    desc = numeric_df.describe().T

    if not desc.empty:
        media_total = round(desc['mean'].mean(), 2)
        insights.append(f"📊 Média geral dos valores: <b>{media_total}</b>")

        melhor_coluna = desc['mean'].idxmax()
        insights.append(f"🏆 Coluna com maior média: <b>{melhor_coluna}</b>")

        max_global = numeric_df.max().max()
        insights.append(f"📈 Maior valor detectado: <b>{max_global}</b>")

        variacao = round(desc['std'].mean(), 2)
        insights.append(f"📉 Variação média (desvio padrão): <b>{variacao}</b>")

    if label_col:
        insights.insert(0, f"🗺️ Coluna usada como referência geográfica: <b>{label_col}</b>")

    # --- 🧾 Tabela HTML formatada ---
    table_html = df.to_html(
        classes="table table-striped table-hover",
        index=False,
        justify='center'
    )

    # --- Renderiza o template ---
    return render(request, 'visualize.html', {
        'chart_data_json': json.dumps(chart_data),
        'table_html': table_html,
        'filename': getattr(excel_file, 'name', 'arquivo'),
        'insights': insights
    })

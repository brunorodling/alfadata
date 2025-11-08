import io
import pandas as pd
from django.shortcuts import render, redirect
from .forms import UploadExcelForm
from django.views.decorators.csrf import csrf_exempt
import json


def upload_file(request):
    form = UploadExcelForm()
    return render(request, 'upload.html', {'form': form})


def visualize(request):
    """
    Recebe POST com arquivo Excel, lê com pandas e prepara dados para Chart.js.
    Agora otimizada para lidar com arquivos grandes de forma segura e leve.
    """
    if request.method != 'POST' or 'excel_file' not in request.FILES:
        return redirect('alfadata:upload')

    excel_file = request.FILES['excel_file']

    try:
        # Leitura eficiente do Excel
        df = pd.read_excel(excel_file, engine='openpyxl')
    except Exception as e:
        return render(request, 'upload.html', {
            'form': UploadExcelForm(),
            'error': f'Erro ao ler Excel: {e}'
        })

    # Limitar número de linhas (protege contra planilhas gigantes)
    max_rows = 2000
    if len(df) > max_rows:
        df = df.head(max_rows)

    # Seleciona apenas colunas numéricas
    numeric_df = df.select_dtypes(include='number')
    if numeric_df.empty:
        return render(request, 'upload.html', {
            'form': UploadExcelForm(),
            'error': 'Nenhuma coluna numérica encontrada no arquivo.'
        })

    # Eixo X (índice ou contagem)
    x_labels = numeric_df.index.astype(str).tolist()

    # Constrói datasets para Chart.js
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

    # Gera tabela HTML
        # Gera tabela HTML
    table_html = df.to_html(
        classes="table table-dark table-striped table-hover align-middle text-center",
        index=False,
        justify='center'
    )

    # === 🔍 Geração de insights automáticos ===
    insights = []
    try:
        mean_stats = df.groupby('Curso').mean(numeric_only=True)
        top_evasao = mean_stats['Evasão (%)'].idxmax()
        top_evasao_val = round(mean_stats['Evasão (%)'].max(), 2)

        top_enade = mean_stats['Média ENADE'].idxmax()
        top_enade_val = round(mean_stats['Média ENADE'].max(), 2)

        top_emprego = mean_stats['Empregabilidade (%)'].idxmax()
        top_emprego_val = round(mean_stats['Empregabilidade (%)'].max(), 2)

        insights = [
            f"O curso com maior evasão média é {top_evasao} ({top_evasao_val}%).",
            f"O curso com melhor desempenho ENADE é {top_enade} ({top_enade_val}).",
            f"A melhor empregabilidade média é do curso {top_emprego} ({top_emprego_val}%).",
        ]
    except Exception as e:
        insights = [f"Não foi possível gerar insights: {e}"]

    # === 🔵 Dados para gráficos de pizza ===
    try:
        dist_alunos = df.groupby('Curso')['Alunos Matriculados'].mean().sort_values(ascending=False)
        dist_satisfacao = df.groupby('Curso')['Satisfação (0–10)'].mean().sort_values(ascending=False)
        dist_empregabilidade = df.groupby('Curso')['Empregabilidade (%)'].mean().sort_values(ascending=False)

        pizza_data = {
            'alunos': {
                'labels': dist_alunos.index.tolist(),
                'data': dist_alunos.values.tolist()
            },
            'satisfacao': {
                'labels': dist_satisfacao.index.tolist(),
                'data': dist_satisfacao.values.tolist()
            },
            'empregabilidade': {
                'labels': dist_empregabilidade.index.tolist(),
                'data': dist_empregabilidade.values.tolist()
            }
        }
    except Exception as e:
        pizza_data = {'error': str(e)}

    return render(request, 'visualize.html', {
        'chart_data_json': json.dumps(chart_data),
        'pizza_data_json': json.dumps(pizza_data),
        'insights': insights,
        'table_html': table_html,
        'filename': getattr(excel_file, 'name', 'arquivo')
    })


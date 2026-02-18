# DATAKENGINEERLAB v1.0

<div align="center">

<img width="250" height="500" alt="spyder" src="https://github.com/user-attachments/assets/d8afc207-bd10-43bb-b6ee-139bc55ff1db" />

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

**Laboratório Analítico Empresarial para Análise de Dados**

[Funcionalidades](#-funcionalidades) • [Instalação](#-instalação) • [Uso](#-uso) • [Screenshots](#-screenshots)

</div>

---

## Sobre o Projeto

O **DATAKENGINEERLAB** é uma aplicação desktop completa para análise de dados, desenvolvida em Python com interface gráfica moderna e intuitiva. Permite importar, visualizar, filtrar e analisar dados de forma profissional sem necessidade de programação.

---

## 🛠️ Tecnologias Utilizadas

- **Python 3.8+**: Linguagem principal
- **Tkinter**: Interface gráfica nativa
- **Pandas**: Manipulação de dados
- **NumPy**: Computação numérica
- **Scikit-learn**: Machine Learning (Rating, Regressão)
- **SciPy**: Estatísticas avançadas (skew, kurtosis, zscore)
- **Matplotlib**: Visualização de gráficos
- **OpenPyXL**: Leitura/escrita Excel
- **PyArrow**: Suporte a Parquet (opcional)

---

### Principais Características

- 📊 **Análises Estatísticas** completas (média, mediana, desvio, correlação, outliers, regressão)
- **Filtro Duplo** por colunas E linhas
- 📑 **Suporte a Múltiplas Abas** do Excel
- 💾 **Exportação** em múltiplos formatos (CSV, Excel, Parquet, JSON)
- **Processamento em Thread** para não travar a interface

---

## Funcionalidades

### 📊 Dados & Preview
- Importação de Excel (.xlsx, .xls) e CSV
- Visualização em grade com scroll
- Seleção de abas em arquivos Excel com múltiplas sheets
- Informações de memória e dimensões da tabela
- Ícones indicativos (📑 múltiplas abas / 📄 aba única)

### ⭐⭐⭐ Rating ML
- Cálculo de score ponderado com Machine Learning
- Seleção de colunas
- Heatmap de cores (verde = alto, vermelho = baixo)
- Normalização MinMax (0-100)
- Ordenação automática por score

### 📈 Estatísticas
- **Coluna ID**: Identificação de registros (texto ou número)
- **Filtro de Colunas**: Seleção múltipla com checkboxes e scroll
- **Filtro de Linhas**:
  - Todas as linhas
  - 🔢 Por índice (range)
  - 🔤 Por valor (operadores: ==, !=, >, <, >=, <=, contains)
  - 🎲 Amostragem aleatória
- **Análises Disponíveis**:
  - 📊 Estatísticas Descritivas (média, mediana, desvio, mínimo, máximo, assimetria, curtose)
  - 🔗 Matriz de Correlação
  - 🚨 Outliers IQR (Intervalo Interquartil)
  - 🚨 Outliers Z-Score
  - 📈 Regressão Linear (com gráfico)

### 🔧 Engenharia de Dados
- **Join/Merge**: União de tabelas (inner, left, right, outer)
- **SQL Engine**: Consultas SQL diretas na tabela ativa
- Exportação de resultados

### 💾 Exportação Universal
- CSV (UTF-8 com BOM)
- Excel (.xlsx)
- Parquet (alta performance)
- JSON (formato indentado)
- Botão de salvamento em todas as abas

---

## 📦 Instalação

### Pré-requisitos

- Python 3.8 ou superior
- pip (gerenciador de pacotes Python)

### Passo a Passo

1. **Clone ou baixe o repositório:**
```bash
git clone https://github.com/seu-usuario/datakenengineerlab.git
cd datakenengineerlab
```

2. **Instale as dependências:**
```bash
# Instalação completa
pip install pandas numpy scikit-learn matplotlib openpyxl scipy

# Opcional: para suporte a Parquet
pip install pyarrow
```

3. **Execute a aplicação:**
```bash
python datakenengineerlab.py
```

### Instalação Rápida (Windows)

```batch
pip install pandas numpy scikit-learn matplotlib openpyxl scipy pyarrow
python datakenengineerlab.py
```

---

## 📖 Uso

### 1. Importando Dados

1. Clique em **"📂 Importar Excel/CSV"**
2. Selecione o arquivo desejado
3. Se o Excel tiver múltiplas abas, uma janela aparecerá para seleção
4. A tabela aparecerá na lista à esquerda

### 2. Visualizando Dados

1. Selecione uma tabela na lista
2. Visualize o preview à direita
3. Veja informações: linhas, colunas, memória, sheet atual

### 3. Análise de Rating ML

1. Vá para a aba **"⭐ Rating ML"**
2. Clique em **"🔄 Atualizar Colunas"**
3. Marque/desmarque colunas para compor o score
4. Ajuste o peso global (0-1) se necessário
5. Clique em **"Calcular Rating"**
6. Visualize o heatmap colorido
7. Salve o resultado com **"💾 Salvar Resultado"**

### 4. Estatísticas Avançadas

1. Vá para a aba **"📈 Estatísticas"**

2. **Selecione Coluna ID** (opcional):
   - Escolha uma coluna para identificar registros (CPF, Código, Nome, etc.)
   - Pode ser texto ou número

3. **Filtre Colunas** (use scroll se necessário):
   - Marque as colunas numéricas para análise
   - Use **"✅ Todas"** ou **"❌ Nenhuma"** para seleção rápida
   - Clique em **"🔄 Atualizar"** para recarregar lista

4. **Filtre Linhas**:
   - **📋 Todas**: Analisa todos os registros
   - **🔢 Por Índice**: Ex: de 0 até 100
   - **🔤 Por Valor**: Ex: status == "ativo" ou valor > 1000
   - **🎲 Amostra**: Ex: 100 linhas aleatórias

5. **Execute Análise** (use scroll para ver todas):
   - **📊 Descritivas**: Estatísticas básicas
   - **🔗 Correlação**: Matriz de correlação + heatmap
   - **🚨 Outliers IQR**: Detecção por intervalo interquartil
   - **🚨 Outliers Z-Score**: Detecção por desvio padrão
   - **📈 Regressão Linear**: Modelo de regressão + gráfico

6. **Salve Resultados**:
   - Clique em **"💾 Salvar Stats"**
   - Ou use o botão em cada janela de resultado

### 5. Engenharia de Dados

**Join entre Tabelas:**
1. Vá para **"🔧 Engenharia (Join/SQL)"**
2. Selecione Tabela A e Tabela B
3. Defina as chaves de junção
4. Escolha o tipo: inner, left, right, outer
5. Clique em **"Executar Join"**

**SQL Query:**
1. Na mesma aba, digite a query SQL
2. Exemplo: `SELECT * FROM data WHERE valor > 1000`
3. Clique em **"Executar SQL"**
4. Resultado vira nova tabela

### 6. Exportação

**Em qualquer aba:**
1. Clique no botão **"💾 Salvar Dados"** (header)
2. Ou use **"💾 Exportar Esta Tabela"**
3. Escolha o formato: CSV, Excel, Parquet ou JSON
4. Selecione o local e salve

---

## 📋 Requisitos do Sistema

- **Sistema Operacional**: Windows 7+, Linux, macOS
- **Python**: 3.8 ou superior
- **RAM**: Mínimo 2GB (recomendado 4GB+)
- **Tela**: Resolução mínima 1280x720

---

## 🔧 Configuração

### Temas e Cores

O sistema usa tema escuro por padrão. Para personalizar, edite o dicionário `THEME` no início do código:

```python
THEME = {
    "bg": "#121212",          # Fundo principal
    "panel": "#1e1e1e",       # Painéis
    "fg": "#e0e0e0",          # Texto
    "accent": "#00e676",      # Cor de destaque (verde)
    "accent_dark": "#00b359", # Destaque escuro
    "border": "#333333",      # Bordas
    "error": "#cf6679",       # Erros
    "warning": "#ff9800",     # Alertas
}
```

### Logs

Os logs são exibidos no painel inferior e também podem ser configurados:

```python
logging.basicConfig(
    level=logging.INFO,  # DEBUG, INFO, WARNING, ERROR
    format='%(asctime)s - %(levelname)s - %(message)s'
)
```

---

### Interface travando
- ✅ **Já otimizado**: Processamento em threads separadas
- Verifique se o arquivo não é muito grande (>100k linhas)
- Use filtro de amostragem para testes

### Scroll não aparece
- Verifique se há conteúdo suficiente para rolar
- Ajuste a altura dos canvases se necessário:
  - Rating cols: `height=150`
  - Stats cols: `height=120`
  - Stats btns: `height=180`

---

## 🔄 Histórico de Versões

### v1.0
- ✅ Otimização de layout e performance
- ✅ Correção de bugs de AttributeError

---

## 📄 Licença

Este projeto está licenciado sob a **Licença MIT** - veja o arquivo [LICENSE](LICENSE) para detalhes.

---

<div align="center">

**by k.**

</div>

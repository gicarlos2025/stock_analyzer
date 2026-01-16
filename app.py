import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import date, timedelta
import locale

# --- Configuração da Página ---
st.set_page_config(
    page_title="Painel de Ações Simples",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CSS Personalizado ---
st.markdown("""
<style>
    /* Variáveis Globais */
    :root {
        --primary-color: #00C897;
        --secondary-color: #FF4D4D;
        --background-light: #F8F9FD;
        --card-background: #FFFFFF;
        --text-primary: #2D3748;
        --text-secondary: #718096;
        --border-radius: 12px;
        --box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
    }

    .stApp {
        background-color: var(--background-light);
        font-family: 'Inter', sans-serif;
    }

    /* Cards de KPI (Topo) */
    div[data-testid="stMetric"] {
        background-color: var(--card-background);
        padding: 20px;
        border-radius: var(--border-radius);
        box-shadow: var(--box-shadow);
        border-left: 5px solid var(--primary-color);
        text-align: center;
        width: 100%;
    }
    
    /* Ajuste de Alinhamento (Padding do Topo) */
    .block-container {
        padding-top: 5rem; /* Ajustado levemente para acomodar o título */
        padding-bottom: 2rem;
    }
    
    /* Estilo do Título Principal */
    h1 {
        color: var(--text-primary);
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Barra Lateral ---
with st.sidebar:
    st.header("Entre com Ação e Período")
    ticker = st.text_input("Símbolo da Ação", value="PETR4.SA")
    
    data_padrao_inicio = date.today() - timedelta(days=800)
    data_inicio = st.date_input("Data de Início", value=data_padrao_inicio, format="DD/MM/YYYY")
    data_fim = st.date_input("Data de Fim", value=date.today(), format="DD/MM/YYYY")
    
    st.button("Atualizar Dados 🔄", type="primary")

# --- Funções Auxiliares ---
def get_price_at_date(df, target_date):
    if target_date in df.index:
        return df.loc[target_date]['Close']
    else:
        try:
            return df.loc[:target_date].iloc[-1]['Close']
        except:
            return None

# --- Lógica Principal ---
try:
    # --- TÍTULO PRINCIPAL ADICIONADO AQUI ---
    st.title("Painel de Ações Simples")

    # Baixar dados
    df = yf.download(ticker, start=data_inicio, end=data_fim, progress=False)
    
    if df.empty:
        st.error(f"Não foi possível encontrar dados para {ticker}. Verifique o símbolo.")
    else:
        if isinstance(df.columns, pd.MultiIndex):
            df = df.xs(ticker, axis=1, level=1)
        
        # --- 1. Seção de KPIs (Topo) ---
        ultimo_fechamento = df['Close'].iloc[-1]
        penultimo_fechamento = df['Close'].iloc[-2]
        
        diff_valor = ultimo_fechamento - penultimo_fechamento
        diff_pct = ((ultimo_fechamento - penultimo_fechamento) / penultimo_fechamento) * 100
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Preço Atual", f"R$ {ultimo_fechamento:.2f}")
        with col2:
            st.metric("Variação (1 dia)", f"R$ {diff_valor:.2f}")
        with col3:
            st.metric("Mudança Percentual", f"{diff_pct:.2f}%")

        # --- 2. Layout Principal (Gráfico + Tabela) ---
        st.markdown("<br>", unsafe_allow_html=True) 
        
        col_main, col_side = st.columns([2, 1])

        # --- Gráfico ---
        with col_main:
            st.markdown("### Histórico de Preço")
            fig = go.Figure(data=[go.Candlestick(
                x=df.index,
                open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name=ticker
            )])
            
            fig.update_layout(
                xaxis_rangeslider_visible=False,
                template="plotly_white",
                margin=dict(l=20, r=20, t=20, b=20),
                height=400,
                hovermode="x unified"
            )
            fig.update_traces(increasing_line_color='#00C897', decreasing_line_color='#FF4D4D')
            st.plotly_chart(fig, use_container_width=True)

        # --- Tabela de Rentabilidade ---
        with col_side:
            st.markdown("### Rentabilidade Acumulada (%)")
            
            hoje = df.index[-1]
            datas_alvo = {
                "Último Mês": hoje - timedelta(days=30),
                "Últimos 3 Meses": hoje - timedelta(days=90),
                "Últimos 6 Meses": hoje - timedelta(days=180),
                "Últimos 12 Meses": hoje - timedelta(days=365),
                "Últimos 24 Meses": hoje - timedelta(days=730)
            }
            
            resultados = []
            preco_atual = df['Close'].iloc[-1]
            
            for periodo, data_alvo in datas_alvo.items():
                preco_antigo = get_price_at_date(df, data_alvo)
                if preco_antigo:
                    rentabilidade = ((preco_atual - preco_antigo) / preco_antigo) * 100
                    resultados.append({"Período": periodo, "Retorno": f"{rentabilidade:.2f}%"})
                else:
                    resultados.append({"Período": periodo, "Retorno": "-"})
            
            st.dataframe(
                pd.DataFrame(resultados),
                hide_index=True,
                use_container_width=True
            )
            
            st.markdown("### Estatísticas")
            stats = pd.DataFrame({
                "Indicador": ["Mínima", "Máxima", "Volume Médio"],
                "Valor": [
                    f"R$ {df['Low'].min():.2f}",
                    f"R$ {df['High'].max():.2f}",
                    f"{df['Volume'].mean():,.0f}"
                ]
            })
            st.dataframe(stats, hide_index=True, use_container_width=True)

except Exception as e:
    st.error(f"Erro ao carregar dados: {e}")
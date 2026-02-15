import streamlit as st
import time
from datetime import datetime
import locale
import pandas as pd

# Importando os módulos do nosso sistema
import ai_engine
import db_manager
import response_engine

# ==============================================================================
# 1. CONFIGURAÇÃO DA PÁGINA E ESTILO (CSS)
# ==============================================================================
st.set_page_config(
    page_title="DeepBox AI - Gestão de Estoque",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Ajustado
st.markdown("""
<style>
    /* Remove o padding excessivo do topo */
    .block-container {
        padding-top: 2rem;
        padding-bottom: 5rem;
    }
    
    /* Esconde o menu 'hamburger' e rodapé */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Estilo para as mensagens */
    .stChatMessage {
        border-radius: 10px;
        margin-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# 2. FUNÇÕES AUXILIARES
# ==============================================================================
def obter_data_extenso():
    """Retorna a data atual formatada"""
    try:
        locale.setlocale(locale.LC_TIME, 'pt_BR.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_TIME, 'Portuguese_Brazil')
        except:
            pass
    return datetime.now().strftime("%A, %d de %B de %Y")

def reset_chat():
    """Limpa o histórico da sessão"""
    st.session_state.messages = []
    st.session_state.sql_debug = None

# ==============================================================================
# 3. BARRA LATERAL (SIDEBAR)
# ==============================================================================
with st.sidebar:
    try:
        st.image("deepbox-logo.jpg", use_container_width=True) 
    except:
        st.title("📦 DeepBox AI")
    
    st.markdown("---")
    st.write("**Assistente de Estoque Inteligente**")
    st.write("Faça perguntas sobre inventário e sazonalidade.")
    
    st.markdown("### ⚙️ Controles")
    
    if st.button("🗑️ Limpar Conversa", use_container_width=True):
        reset_chat()
        st.rerun()

    mostrar_debug = st.checkbox("🛠️ Modo Debug (Ver SQL)", value=False)
    
    st.markdown("---")
    st.caption(f"📅 Data do Sistema:\n{obter_data_extenso()}")
    st.caption("v.3.2 - Stable")

# ==============================================================================
# 4. LÓGICA PRINCIPAL DO CHAT
# ==============================================================================

if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({
        "role": "assistant", 
        "content": "Olá! Sou seu assistente de estoque. 📦\n\nPosso ajudar com consultas de saldo, sugestões de compra e análise de sazonalidade. O que você precisa saber hoje?"
    })

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "sql" in message and mostrar_debug:
            with st.expander("🔍 Ver SQL Gerado"):
                st.code(message["sql"], language="sql")

# ==============================================================================
# 5. CAPTURA DA PERGUNTA DO USUÁRIO
# ==============================================================================
if prompt := st.chat_input("Digite sua pergunta aqui..."):
    
    # 1. Exibe a pergunta do usuário
    with st.chat_message("user"):
        st.markdown(prompt)
    
    st.session_state.messages.append({"role": "user", "content": prompt})

    # 2. Processamento da IA
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        
        # Status Interativo
        with st.status("Processando...", expanded=True) as status:
            
            # --- ETAPA 1: Geração de SQL ---
            status.write("🧠 Interpretando pergunta...")
            data_atual = obter_data_extenso()
            query_sql = ai_engine.gerar_query_sql(prompt, data_atual)
            
            if not query_sql:
                status.update(label="Erro na interpretação", state="error")
                resposta_final = "Não consegui entender como traduzir isso para o banco de dados."
                sql_gerado = None
            else:
                # --- ETAPA 2: Consulta ao Banco ---
                status.write("🗄️ Consultando banco de dados...")
                dados_brutos = db_manager.executar_consulta(query_sql)
                
                if isinstance(dados_brutos, str) and "Erro" in dados_brutos:
                    # AQUI ESTAVA O ERRO POTENCIAL DE QUEBRA DE LINHA
                    status.update(label="Erro no Banco de Dados", state="error")
                    resposta_final = f"Erro técnico ao consultar o banco: {dados_brutos}"
                    sql_gerado = query_sql
                else:
                    # --- ETAPA 3: Análise Final ---
                    status.write("🤖 Analisando dados...")
                    resposta_final = response_engine.gerar_resposta_final(prompt, dados_brutos)
                    sql_gerado = query_sql
                    status.update(label="Concluído!", state="complete", expanded=False)

        # Exibe a resposta final
        message_placeholder.markdown(resposta_final)
        
        if mostrar_debug and sql_gerado:
            with st.expander("🔍 Ver SQL Gerado nesta interação"):
                st.code(sql_gerado, language="sql")

    # Salva histórico
    st.session_state.messages.append({
        "role": "assistant", 
        "content": resposta_final,
        "sql": sql_gerado
    })
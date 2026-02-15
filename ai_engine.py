import google.generativeai as genai
import os
from dotenv import load_dotenv
from prompts import SCHEMA_ESTOQUE, PROMPT_GERADOR_SQL

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da IA com segurança
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)

# Nota: Verifique se o nome do modelo 'gemini-2.5-flash' está correto para sua conta.
# Geralmente os públicos são 'gemini-1.5-flash' ou 'gemini-2.5-flash'.
model = genai.GenerativeModel('gemini-2.5-flash') 

def gerar_query_sql(pergunta_usuario, data_atual):
    """
    Recebe a pergunta natural e a data de hoje, retornando a query SQL limpa.
    """
    try:
        # Montagem do prompt com schema, pergunta e DATA
        prompt_completo = PROMPT_GERADOR_SQL.format(
            schema=SCHEMA_ESTOQUE, 
            pergunta=pergunta_usuario,
            data_atual=data_atual  # <--- NOVA INJEÇÃO DE DADO
        )
        
        # Chamada ao modelo
        response = model.generate_content(prompt_completo)
        texto_ia = response.text.strip()
        
        # Limpeza rigorosa para garantir que o MySQL não receba lixo
        query = texto_ia.replace('```sql', '').replace('```', '').replace(';', '')
        
        # Filtro de segurança: Garante que a query comece com SELECT
        if "SELECT" in query.upper():
            query = query[query.upper().find("SELECT"):]
        
        return query.strip()
    
    except Exception as e:
        print(f"❌ Erro na Geração de SQL: {e}")
        return None
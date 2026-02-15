import google.generativeai as genai
import os
from dotenv import load_dotenv
from prompts import PROMPT_RESPOSTA_FINAL

# Carregar variáveis de ambiente
load_dotenv()

# Configuração da IA
api_key = os.getenv('GEMINI_API_KEY')
genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-2.5-flash')

def gerar_resposta_final(pergunta_usuario, dados_banco):
    """
    Cruza os dados do banco com a pergunta original para gerar a resposta final.
    """
    try:
        # Caso o banco retorne erro ou nada seja encontrado
        if not dados_banco or (isinstance(dados_banco, str) and "Erro" in dados_banco):
            return "Desculpe, não consegui encontrar informações no banco de dados para responder a essa pergunta."

        # Injeção de dados no prompt de resposta
        prompt_completo = PROMPT_RESPOSTA_FINAL.format(
            pergunta=pergunta_usuario,
            dados=dados_banco
        )
        
        # Geração da resposta em linguagem natural
        response = model.generate_content(prompt_completo)
        
        return response.text.strip()

    except Exception as e:
        print(f"❌ Erro na Geração da Resposta Natural: {e}")
        return "Houve um erro técnico ao processar sua resposta. Por favor, tente novamente."
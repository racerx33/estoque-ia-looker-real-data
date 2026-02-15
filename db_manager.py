import mysql.connector
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações de conexão obtidas do ambiente (Foco em segurança)
DB_CONFIG = {
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASS'),
    'host': os.getenv('DB_HOST'),
    'database': os.getenv('DB_NAME'),
    'auth_plugin': 'mysql_native_password' # Garante compatibilidade com diversos servidores
}

def executar_consulta(sql_query):
    """
    Conecta ao banco MySQL, executa a query gerada pela IA e retorna os resultados.
    """
    conn = None
    try:
        # 1. Estabelece a conexão
        conn = mysql.connector.connect(**DB_CONFIG)
        
        # 2. Cria o cursor com dictionary=True para facilitar a leitura pela IA na fase 2
        cursor = conn.cursor(dictionary=True)
        
        # Log para monitoramento interno (importante para o PMO auditar a IA)
        print(f"\n[INFO] Acessando Banco: {DB_CONFIG['database']}")
        print(f"[SQL] Executando comando: {sql_query}")
        
        # 3. Execução
        cursor.execute(sql_query)
        
        # 4. Recuperação dos resultados
        resultados = cursor.fetchall()
        
        return resultados

    except mysql.connector.Error as err:
        # Tratamento específico de erros comuns de banco de dados
        erro_msg = f"Erro de Banco de Dados: {err.errno} - {err.msg}"
        print(f"❌ {erro_msg}")
        return erro_msg

    except Exception as e:
        erro_msg = f"Erro Geral de Conexão: {str(e)}"
        print(f"❌ {erro_msg}")
        return erro_msg

    finally:
        # 5. Garante o fechamento da conexão para não esgotar o pool do servidor
        if conn and conn.is_connected():
            cursor.close()
            conn.close()
            print("[INFO] Conexão MySQL encerrada com segurança.")

# Bloco de teste rápido (opcional)
if __name__ == "__main__":
    # Teste de conectividade simples
    teste = executar_consulta("SELECT COUNT(*) as total FROM fato_estoque_Vendas")
    print(f"Resultado do teste: {teste}")
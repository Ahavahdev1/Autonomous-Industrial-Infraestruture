import os
import logging

# Configuração global e thread-safe do Log de Auditoria Isolado
logging.basicConfig(
    filename="system_audit.log",
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    encoding="utf-8"
)

def carregar_env_nativo():
    """Carrega as variáveis do arquivo .env local para o ambiente."""
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    val_limpo = val.strip().strip("'").strip('"')
                    os.environ[key.strip()] = val_limpo

carregar_env_nativo()
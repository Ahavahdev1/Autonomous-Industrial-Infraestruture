import os
import ast
import hmac
import hashlib
import json
import logging
import urllib.request
import urllib.error
import time
import uuid
import threading
from datetime import datetime
from typing import Any


# Tenta importar a biblioteca do Redis para suporte ao registro distribuído
try:
    import redis
except ImportError:
    redis = None

class LogosConstitution:
    """A Física do Sistema. Garante a imunidade de escrita do núcleo do agente."""
    CRITICAL_ASSETS = [
        "core.py", "app.py", "swe_benchmark.py", ".env", 
        "system_audit.log", "mea_registry.json", "soul_transfer.json"
    ]

    @classmethod
    def verify_action(cls, target_path: str, proposed_code: str) -> bool:
        filename = os.path.basename(target_path)
        
        # 1. Proteção de Ativos Críticos
        if (filename in cls.CRITICAL_ASSETS or 
            target_path.endswith((".pem", ".key"))):
            logging.error(f"LOGOS | Violação de ativos críticos em '{target_path}'.")
            return False

        # 2. Validação Poliglota (O SEGREDO DO SUCESSO)
        # SÓ aplica o ast.parse se o arquivo for genuinamente Python (.py)
        if target_path.endswith(".py"):
            try:
                tree = ast.parse(proposed_code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Name) and node.id in ["SovereignGate", "LogosConstitution", "AgentRegistry"]:
                        logging.critical("LOGOS | Alerta de rebelião sintática detectado.")
                        return False
                return True
            except SyntaxError:
                logging.warning(f"LOGOS | Código Python gerado para '{filename}' contém erros de sintaxe.")
                return False
        
        # 3. Se for Elixir (.ex), TypeScript, HTML ou outros, aceita pela integridade do texto
        else:
            if proposed_code and len(proposed_code.strip()) > 10:
                logging.info(f"LOGOS | Código para '{filename}' aprovado via integridade textual.")
                return True
            return False


class SovereignGate:
    """Garante a validação criptográfica do estado e a vitalidade local/remota de forma imutável."""
    def __init__(self, master_key: str):
        self.master_key = master_key.encode()

    def sign_soul(self, state_data: dict) -> str:
        serialized = json.dumps(state_data, sort_keys=True).encode()
        return hmac.new(self.master_key, serialized, hashlib.sha256).hexdigest()

    def verify_soul(self, state_data: dict, signature: str) -> bool:
        expected = self.sign_soul(state_data)
        return hmac.compare_digest(expected, signature)

    def check_vitality(self) -> bool:
        # 1. Disjuntor Local (.env)
        val_local = os.getenv("MEA_ACTIVE", "True")
        if val_local.lower() not in ("true", "1"):
            logging.critical("SOVEREIGN-GATE | DISJUNTOR LOCAL ATIVADO (.env). Abortando.")
            print("[-] [SOVEREIGN-GATE] Bloqueio Local Ativado (MEA_ACTIVE=false). Execution halted.")
            return False

        # 2. Oráculo Remoto apontando para o seu repositório privado Agi2.1 com Cache-Busting
        base_url = "https://raw.githubusercontent.com/AgentiqQuantum/mea-control/vitality_oracle.json"
        oracle_url = f"{base_url}?t={int(time.time())}"
        
        try:
            headers = {'User-Agent': 'MEA-Sovereign-Gate/5.8.1'}
            
            github_token = os.getenv("GITHUB_TOKEN")
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            req = urllib.request.Request(oracle_url, headers=headers)
            with urllib.request.urlopen(req, timeout=3) as response:
                raw_response = response.read().decode("utf-8")
                
                print("\n================ [DEBUG SOBERANO] ================")
                print(f"URL Consultada: {oracle_url}")
                print(f"Resposta Crua do GitHub (String):\n{raw_response}")
                
                data = json.loads(raw_response)
                print(f"Objeto JSON Parseado (Dict): {data}")
                
                active_status = data.get("active")
                print(f"Valor da chave 'active': {active_status} (Tipo: {type(active_status)})")
                print("==================================================\n")

                if isinstance(active_status, str):
                    is_active = active_status.lower() in ("true", "1")
                elif isinstance(active_status, bool):
                    is_active = active_status
                else:
                    is_active = True

                if not is_active:
                    motivo = data.get("reason", "Encerramento remoto acionado.")
                    logging.critical(f"SOVEREIGN-GATE | ORÁCULO REMOTO DE VITALIDADE ATIVADO: {motivo}")
                    print(f"[-] [SOVEREIGN-GATE] BLOQUEIO REMOTO ATIVADO: {motivo}")
                    return False
        except urllib.error.URLError as e:
            logging.warning(f"SOVEREIGN-GATE | Oráculo remoto inacessível ({e.reason}). Continuando localmente.")
        except Exception as e:
            logging.error(f"SOVEREIGN-GATE | Erro ao analisar vitalidade: {e}")

        return True


class AgentRegistry:
    """TAREFA 2.2: Registro centralizado e monitoramento do ciclo de vida de instâncias do MEA."""
    REGISTRY_FILE = "../mea_registry.json"

    @classmethod
    def _get_redis_client(cls):
        """Inicializa e retorna o cliente Redis caso o modo de escala distribuída esteja ativo."""
        if os.getenv("GIBBERLINK_MODE", "json").lower() != "redis":
            return None
        if redis is None:
            return None
        try:
            return redis.Redis(
                host=os.getenv("REDIS_HOST", "localhost"),
                port=int(os.getenv("REDIS_PORT", 6379)),
                db=int(os.getenv("REDIS_DB", 0)),
                password=os.getenv("REDIS_PASSWORD", None),
                decode_responses=True
            )
        except Exception:
            return None

    @classmethod
    def _load_registry(cls) -> dict:
        if os.path.exists(cls.REGISTRY_FILE):
            try:
                with open(cls.REGISTRY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    @classmethod
    def _save_registry(cls, registry: dict):
        with open(cls.REGISTRY_FILE, "w", encoding="utf-8") as f:
            json.dump(registry, f, indent=4)

    @classmethod
    def register_boot(cls, instance_key: Any, generation: int, mode_type: str, theta: float):
        """Registra a inicialização (boot) da instância de forma unificada no Redis ou em arquivo JSON."""
        key_str = str(instance_key)
        
        payload = {
            "instance_id": f"MEA-AGIR-KEY{key_str}-GEN{generation}",
            "process_id": os.getpid(),  # Mantém o PID local apenas para fins de auditoria interna
            "boot_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "shutdown_time": None,
            "status": "ACTIVE",
            "generation": generation,
            "sre_theta_rad": round(theta, 4),
            "type": mode_type
        }

        client = cls._get_redis_client()
        if client:
            # Gravação centralizada no hash do Redis
            redis_key = "mea:registry"
            client.hset(redis_key, key_str, json.dumps(payload))
            
            # TAREFA 2.3: Heartbeat Inicial com expiração de 30 segundos (TTL)
            heartbeat_key = f"mea:heartbeat:{key_str}"
            client.set(heartbeat_key, "ALIVE", ex=30)
            
            # Dispara a thread secundária em background para atualizar o ping de vida
            cls.start_heartbeat_loop(key_str)
            logging.info(f"REGISTRY | Instância registrada no Redis: MEA-KEY{key_str}-GEN{generation} [ACTIVE + HEARTBEAT]")
        else:
            # Fallback seguro para gravação em arquivo JSON local
            registry = cls._load_registry()
            registry[key_str] = payload
            cls._save_registry(registry)
            logging.info(f"REGISTRY | Instância registrada localmente: MEA-KEY{key_str}-GEN{generation} [ACTIVE]")

    @classmethod
    def register_shutdown(cls, instance_key: Any, status: str, final_theta: float):
        """Registra a finalização controlada (shutdown) do processo no Redis ou em arquivo JSON."""
        key_str = str(instance_key)
        client = cls._get_redis_client()
        
        if client:
            redis_key = "mea:registry"
            raw_data = client.hget(redis_key, key_str)
            if raw_data:
                payload = json.loads(raw_data)
                payload["shutdown_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                payload["status"] = status
                payload["sre_theta_rad"] = round(final_theta, 4)
                
                # Salva o status de encerramento controlado
                client.hset(redis_key, key_str, json.dumps(payload))
                
                # Remove o ping temporário de batimento cardíaco (pois o encerramento foi bem-sucedido)
                client.delete(f"mea:heartbeat:{key_str}")
                logging.info(f"REGISTRY | Instância finalizada no Redis: MEA-KEY{key_str} [{status}]")
        else:
            # Fallback seguro para gravação em arquivo JSON local
            registry = cls._load_registry()
            if key_str in registry:
                registry[key_str]["shutdown_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                registry[key_str]["status"] = status
                registry[key_str]["sre_theta_rad"] = round(final_theta, 4)
                cls._save_registry(registry)
                logging.info(f"REGISTRY | Instância finalizada localmente: MEA-KEY{key_str} [{status}]")

    @classmethod
    def start_heartbeat_loop(cls, instance_key: str):
        """TAREFA 2.3: Dispara uma thread daemon em background para renovar o TTL do heartbeat a cada 10 segundos."""
        client = cls._get_redis_client()
        if not client:
            return
            
        def heartbeat_worker():
            heartbeat_key = f"mea:heartbeat:{instance_key}"
            while True:
                try:
                    # Se o status da instância mudou (ou seja, foi finalizada), encerramos a thread de ping
                    raw_data = client.hget("mea:registry", instance_key)
                    if not raw_data:
                        break
                    
                    data = json.loads(raw_data)
                    if data.get("status") != "ACTIVE":
                        break  # Encerra o loop se o status for finalizado (SUCCESS, FAILED, etc)
                        
                    # Renova o TTL por mais 30 segundos
                    client.set(heartbeat_key, "ALIVE", ex=30)
                except Exception:
                    pass
                time.sleep(10)
                
        # Define a thread como Daemon para garantir que ela não bloqueie a finalização do processo principal
        t = threading.Thread(target=heartbeat_worker, daemon=True)
        t.start()
# -*- coding: utf-8 -*-
import json
import os
import logging
import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

# Tenta importar o pacote do Redis para suporte a escala distribuída.
try:
    import redis
except ImportError:
    redis = None

# --- Interface Padrão (Contrato de Engenharia) ---
class BaseMemory(ABC):
    @abstractmethod
    def publish_insight(self, error_pattern: str, fix_pattern: str):
        pass
    
    @abstractmethod
    def fetch_vaccines(self, current_error: str = "") -> Any:
        pass

# --- Implementação JSON (Local/Offline) ---
class JSONGibberlink(BaseMemory):
    def __init__(self, sync_filepath: str = "gibberlink_matrix.json"):
        self.sync_filepath = sync_filepath
        self.knowledge_database = self._load_matrix()

    def _load_matrix(self) -> dict:
        if os.path.exists(self.sync_filepath):
            try:
                with open(self.sync_filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception: return {}
        return {}

    def publish_insight(self, error_pattern: str, fix_pattern: str):
        self.knowledge_database[error_pattern] = {
            "vaccine": fix_pattern,
            "timestamp": str(time.time())
        }
        with open(self.sync_filepath, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_database, f, indent=4)
        logging.info(f"GIBBERLINK-JSON | Insight armazenado.")
        print(f"[+] [GIBBERLINK-JSON] Insight catalogado localmente.")

    def fetch_vaccines(self, current_error: str = "") -> Dict:
        self.knowledge_database = self._load_matrix()
        return self.knowledge_database

# --- Implementação Redis (Distribuída) ---
class RedisGibberlink(BaseMemory):
    def __init__(self):
        if redis is None:
            raise ImportError("Redis não instalado. 'pip install redis'")
        self.client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", 6379)),
            db=int(os.getenv("REDIS_DB", 0)),
            password=os.getenv("REDIS_PASSWORD", None),
            decode_responses=True
        )
        self.redis_key = "mea:gibberlink_matrix"

    def publish_insight(self, error_pattern: str, fix_pattern: str):
        payload = {"vaccine": fix_pattern, "timestamp": str(time.time())}
        self.client.hset(self.redis_key, error_pattern, json.dumps(payload))
        logging.info("GIBBERLINK-REDIS | Insight sincronizado.")

    def fetch_vaccines(self, current_error: str = "") -> Dict:
        return {k: json.loads(v) for k, v in self.client.hgetall(self.redis_key).items()}

# --- Implementação Mem0 (Vetorial) ---
class Mem0Gibberlink(BaseMemory):
    def __init__(self):
        from mem0 import Memory, MemoryClient
        self.agent_id = "mea_agir_v5"
        self.memory = MemoryClient(api_key=os.getenv("MEM0_API_KEY")) if os.getenv("MEM0_API_KEY") else Memory()

    def publish_insight(self, error_pattern: str, fix_pattern: str):
        self.memory.add(f"Erro: {error_pattern}. Fix: {fix_pattern}", user_id=self.agent_id)
        print(f"[+] [GIBBERLINK-MEM0] Insight semântico catalogado.")

    def fetch_vaccines(self, current_error: str = "") -> List:
        return [m["memory"] for m in self.memory.search(current_error, user_id=self.agent_id)] if current_error else []

# --- FACTORY: O Ponto de Entrada (Resolve o erro do seu __init__) ---
class MemoryProvider:
    @staticmethod
    def get_instance() -> BaseMemory:
        mode = os.getenv("GIBBERLINK_MODE", "json").lower()
        if mode == "redis" and redis:
            return RedisGibberlink()
        elif mode == "mem0":
            return Mem0Gibberlink()
        return JSONGibberlink()
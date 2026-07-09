import os
import json
import logging
from typing import Any

class JSONGibberlink:
    """Implementação clássica da memória local baseada em arquivo JSON."""
    def __init__(self, sync_filepath: str = "gibberlink_matrix.json"):
        self.sync_filepath = sync_filepath
        self.knowledge_database = self._load_matrix()

    def _load_matrix(self) -> dict:
        if os.path.exists(self.sync_filepath):
            try:
                with open(self.sync_filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def publish_insight(self, error_pattern: str, fix_pattern: str):
        self.knowledge_database[error_pattern] = {
            "vaccine": fix_pattern,
            "timestamp": str(os.stat(self.sync_filepath).st_mtime) if os.path.exists(self.sync_filepath) else "now"
        }
        with open(self.sync_filepath, "w", encoding="utf-8") as f:
            json.dump(self.knowledge_database, f, indent=4)
        logging.info(f"GIBBERLINK-JSON | Vacina publicada para: '{error_pattern[:50]}'")
        print(f"[+] [GIBBERLINK-JSON] Insight catalogado localmente.")

    def fetch_vaccines(self, current_error: str = "") -> dict:
        self.knowledge_database = self._load_matrix()
        return self.knowledge_database


class Mem0Gibberlink:
    """Implementação avançada baseada em memória vetorial semântica usando Mem0."""
    def __init__(self):
        from mem0 import Memory
        self.memory = Memory()
        self.agent_id = "mea_agir_v5"

    def publish_insight(self, error_pattern: str, fix_pattern: str):
        learning_context = (
            f"Erro de teste: '{error_pattern[:200]}'. "
            f"Solução aplicada: '{fix_pattern}'"
        )
        self.memory.add(learning_context, user_id=self.agent_id)
        logging.info("GIBBERLINK-MEM0 | Vacina semântica armazenada no banco vetorial.")
        print(f"[+] [GIBBERLINK-MEM0] Insight semântico catalogado.")

    def fetch_vaccines(self, current_error: str = "") -> list:
        if not current_error:
            return []
        memories = self.memory.search(current_error, user_id=self.agent_id)
        return [m["memory"] for m in memories]
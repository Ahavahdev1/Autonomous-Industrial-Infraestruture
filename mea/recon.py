import os
import ast
from typing import Dict, Any, List

class ReconEngine:
    """Executa o mapeamento AST local do repositório para otimização de custo."""
    @staticmethod
    def map_repository(directory: str) -> List[Dict[str, Any]]:
        file_map = []
        for root, _, files in os.walk(directory):
            for file in files:
                # Ignora os scripts de controle e toda a pasta 'mea' para evitar vazamento sintático
                if (file.endswith(".py") and 
                    file not in ["core.py", "app.py", "swe_benchmark.py"] and 
                    "mea" not in root.replace("\\", "/")):
                    
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            tree = ast.parse(f.read())
                        functions = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                        classes = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                        file_map.append({
                            "path": filepath,
                            "functions": functions,
                            "classes": classes
                        })
                    except Exception:
                        pass
        return file_map
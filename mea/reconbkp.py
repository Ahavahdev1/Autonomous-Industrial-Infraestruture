# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA — ReconEngine v10.6.5 (SRE Polyglot Recon Engine)
#  Mapeamento estrutural de bases de código poliglota para otimização de contexto.
#  Copyright (c) 2026 Bruno Loureiro Desidera. All rights reserved.
# ==============================================================================
import os
import ast
import logging
from typing import Dict, Any, List

class ReconEngine:
    """
    Executa o mapeamento estrutural local do repositório para otimização de contexto.
    Suporta as 9 principais linguagens do benchmark global SWE-bench Multilingual.
    """
    # Extensões homologadas pelo ecossistema de testes de múltiplas linguagens
    SUPPORTED_EXTENSIONS = (
        ".py", ".ex", ".go", ".rs", ".java", 
        ".cpp", ".c", ".php", ".rb", ".js", ".ts", ".html"
    )

    @staticmethod
    def map_repository(directory: str) -> List[Dict[str, Any]]:
        """Mapeia arquivos do diretório de forma seletiva ou valida um alvo direto."""
        file_map = []
        
        # 1. PORTÃO DE BYPASS: Se o alvo for um arquivo direto, aceita-o imediatamente
        if os.path.isfile(directory):
            logging.info(f"RECON | Alvo direto de arquivo identificado: '{directory}'")
            return [{"path": directory, "functions": [], "classes": []}]
            
        # 2. VARREDURA DO DIRETÓRIO (Modo Enxame de Colmeia)
        for root, _, files in os.walk(directory):
            # Proteção: Ignora a pasta 'mea' para evitar vazamento sintático
            if "mea" in root.replace("\\", "/"):
                continue
                
            for file in files:
                # Ignora scripts de controle local e arquivos de depuração
                if file in ["core.py", "app.py", "app_MEA.py", "swe_benchmark.py", "failed_patch_debug.txt"] or file.endswith(".bak"):
                    continue
                    
                if file.endswith(ReconEngine.SUPPORTED_EXTENSIONS):
                    filepath = os.path.join(root, file)
                    metadata = {"path": filepath, "functions": [], "classes": []}
                    
                    # 3. EXTRAÇÃO DE METADADOS SINTÁTICOS (Apenas para Python via AST)
                    # Evita tentar compilar Elixir, Go ou Rust como Python no parser estático
                    if file.endswith(".py"):
                        try:
                            with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
                                tree = ast.parse(f.read())
                            metadata["functions"] = [n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
                            metadata["classes"] = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
                        except Exception as e:
                            logging.debug(f"RECON | AST Parse ignorado em {file}: {e}")
                            
                    file_map.append(metadata)
                    
        return file_map
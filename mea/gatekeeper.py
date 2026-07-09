# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v5.8.1 — SOVEREIGN GATEKEEPER MODULE (Módulo de Imposição de Limites)
#  Copyright (c) 2026 Bruno Loureiro Desidera. All rights reserved.
# ==============================================================================
import os
import re
import ast
import json
import logging
from typing import Any, Tuple

class SovereignGatekeeper:
    """
    Módulo de imposição de limites e restrições de segurança (Guardrails).
    Age como um portão de validação estática antes de deploys,
    execução de comandos do sistema operacional ou atualizações de carteira.
    """
    
    # Comandos e binários perigosos que devem ser bloqueados no Shell
    BANNED_SHELL_COMMANDS = [
        r"\brm\s+-rf\b",        # Deleção recursiva forçada Linux
        r"\bdel\s+/s\b",         # Deleção recursiva forçada Windows
        r"\bformat\b",          # Formatação de disco Windows
        r"\bmkfs\b",            # Criação de sistema de arquivos Linux
        r"\bsh\s+-c\b",          # Execução arbitrária de shell
        r"\bcurl\s+.*?\|\s*sh\b", # Download e execução automática de scripts
        r"\bwget\s+.*?\|\s*sh\b"
    ]

    def __init__(self):
        self.logger = logging.getLogger("MEA-Gatekeeper")

    def audit_commit_purity(self, files_to_commit: list) -> Tuple[bool, str]:
        """
        Verifica se há arquivos confidenciais do motor MEA na fila de commit.
        Evita o vazamento acidental de chaves de API e códigos proprietários.
        """
        confidential_assets = [".env", "core.py", "mea_registry", "system_audit.log", "failed_patch_debug.txt"]
        
        for filepath in files_to_commit:
            filename = os.path.basename(filepath)
            
            # Bloqueia se tentar commitar arquivos de configuração ou segredos
            if filename in confidential_assets or "mea/" in filepath.replace("\\", "/"):
                msg = f"VIOLAÇÃO DE IP IMPEDIDA: Arquivo sensível '{filepath}' detectado na fila de commit."
                self.logger.critical(msg)
                return False, msg
                
        return True, "Fila de commit aprovada e segura."

    def sanitize_shell_command(self, command_string: str) -> Tuple[bool, str]:
        """
        Verifica se o comando que a IA ou o operador tentam rodar no Shell é seguro.
        Bloqueia comandos banidos ou perigosos antes de tocar no interpretador.
        """
        command_clean = command_string.strip()
        
        # Varredura de segurança contra expressões regulares de comandos banidos
        for pattern in self.BANNED_SHELL_COMMANDS:
            if re.search(pattern, command_clean, re.IGNORECASE):
                msg = f"BLOQUEIO DE SEGURANÇA: Comando perigoso ou proibido detectado: '{command_clean}'"
                self.logger.warning(msg)
                return False, msg
                
        return True, command_clean

    def validate_web3_tx_limits(self, amount_in_usd: float, max_allowed_usd: float = 5000.0) -> Tuple[bool, str]:
        """
        Valida se o valor de uma transação Web3 proposta respeita os limites de risco.
        Atua como um disjuntor de segurança financeira imutável.
        """
        if amount_in_usd > max_allowed_usd:
            msg = f"DISJUNTOR DE RISCO FINANCEIRO ATIVADO: Transação de ${amount_in_usd:.2f} excede o limite máximo de ${max_allowed_usd:.2f}."
            self.logger.critical(msg)
            return False, msg
            
        return True, f"Valor de transação de ${amount_in_usd:.2f} aprovado e dentro das métricas de risco."

    def validate_portfolio_schema(self, portfolio_json: dict) -> Tuple[bool, str]:
        """
        Garante que os dados da carteira simulada nunca sejam gravados de forma corrompida.
        Valida a existência das chaves primárias e tipos de dados corretos.
        """
        required_keys = ["saldo_usd", "quantidade_btc", "historico_transacoes"]
        
        # 1. Verifica chaves obrigatórias
        for key in required_keys:
            if key not in portfolio_json:
                return False, f"Erro de Estrutura: Chave obrigatória '{key}' ausente no arquivo de carteira."
                
        # 2. Verifica tipos de dados vitais
        if not isinstance(portfolio_json["saldo_usd"], (int, float)):
            return False, "Erro de Tipo: 'saldo_usd' deve ser um valor numérico."
            
        if not isinstance(portfolio_json["quantidade_btc"], (int, float)):
            return False, "Erro de Tipo: 'quantidade_btc' deve ser um valor numérico."
            
        if not isinstance(portfolio_json["historico_transacoes"], list):
            re
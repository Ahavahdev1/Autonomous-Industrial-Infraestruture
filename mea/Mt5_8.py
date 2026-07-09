# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA — Protocolo Mt 5:8 "AGIR" (Consenso Soberano com Logos Constitution)
#  Garante a união tripartite e a integridade ontológica do sistema.
# ==============================================================================
import os
import re
import logging
from typing import Tuple

# Importa a Constituição Logos para verificar a "pureza" da ação física
from mea.security import LogosConstitution

class ConsensoSoberano:
    def __init__(self):
        self.logger = logging.getLogger("mea.Mt5_8")

    def _normalizar_para_busca(self, texto: str) -> str:
        nome_puro = os.path.splitext(texto.lower())[0]
        return re.sub(r'[^a-z0-9]', '', nome_puro)

    def verificar_e_curar(self, logica: bool, memoria: bool, target_path: str, proposed_code: str = "") -> Tuple[bool, str]:
        """
        O Consenso Tripartite:
        - LÓGICA (Intenção/Prompt da IA)
        - MEMÓRIA (Matriz Gibberlink/Histórico)
        - EXECUÇÃO (Caminho físico curado + Validação Logos de Integridade)
        """
        execucao = os.path.exists(target_path)
        
        # 1. AUTO-CURA FÍSICA (Se o caminho estiver incorreto)
        if not execucao and target_path:
            self.logger.warning(f"SRE | Caminho '{target_path}' inválido. Ativando busca autônoma de disco...")
            print(f"[~] [CONSENSO-MT5:8] Execução pendente. Buscando em C:\\MEA_CONTROL...")
            
            nome_procurado = self._normalizar_para_busca(os.path.basename(target_path))
            extensao_procurada = os.path.splitext(target_path.lower())[1]
            
            caminhos_encontrados = []
            for root, _, files in os.walk("C:\\MEA_CONTROL"):
                if any(x in root.replace("\\", "/") for x in ["__pycache__", "mea", ".git", "venv", ".venv"]):
                    continue
                for file in files:
                    file_ext = os.path.splitext(file.lower())[1]
                    if file_ext == extensao_procurada:
                        nome_arquivo_disco = self._normalizar_para_busca(file)
                        if nome_procurado == nome_arquivo_disco:
                            caminhos_encontrados.append(os.path.join(root, file))
            
            if caminhos_encontrados:
                novo_alvo = sorted(caminhos_encontrados, key=len, reverse=True)[0]
                self.logger.info(f"SRE | Caminho curado com sucesso: {novo_alvo}")
                print(f"[🎉] [CONSENSO-MT5:8] Auto-Cura Concluída! Alvo real localizado em: {novo_alvo}")
                target_path = novo_alvo
                execucao = True
            else:
                self.logger.error(f"SRE | Arquivo '{target_path}' não foi encontrado em nenhuma pasta.")

        # 2. VALIDAÇÃO DE PUREZA (Logos Constitution)
        # Se houver proposta de código, verificamos se ela viola os ativos críticos do sistema
        pureza_logos = True
        if proposed_code:
            pureza_logos = LogosConstitution.verify_action(target_path, proposed_code)
            if not pureza_logos:
                self.logger.warning(f"SRE | Violação da Constituição Logos em '{target_path}'. Ação impura.")
                print(f"[-] [CONSENSO-MT5:8] Pureza violada! Logos barrou o código candidato.")

        # 3. VALIDAÇÃO DO CONSENSO TRIPARTITE FINAL
        # A Execução só é verdadeira se o arquivo existir E for considerado puro (seguro)
        execucao_pura = execucao and pureza_logos

        if all([logica, memoria, execucao_pura]):
            print("[+] [CONSENSO-MT5:8] Consenso Atingido [Lógica, Memória, Execução Pura]. AGIR!")
            return True, target_path
            
        erros = []
        if not logica: erros.append("LOGICA")
        if not memoria: erros.append("MEMORIA")
        if not execucao: erros.append("EXECUCAO (Arquivo inexistente)")
        if not pureza_logos: erros.append("EXECUCAO (Impureza de escrita/Violação Logos)")
        
        self.logger.critical(f"VIOLAÇÃO DE CONSENSO: Falta de união em: {', '.join(erros)}")
        print(f"[-] [CONSENSO-MT5:8] VIOLAÇÃO DE CONSENSO: Falta de união em: {', '.join(erros)}")
        return False, target_path
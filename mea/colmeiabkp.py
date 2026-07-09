import os
import sys
import logging
import concurrent.futures
from typing import List
from mea.security import SovereignGate, AgentRegistry
from mea.recon import ReconEngine

# Reutiliza o logger configurado no config.py
logger = logging.getLogger("mea")

class SwarmOrchestrator:
    """A Abelha Rainha. Orquestra, distribui e executa tarefas de reparo em múltiplos arquivos em paralelo."""
    def __init__(self, master_key: str):
        self.master_key = master_key
        self.gate = SovereignGate(master_key)

    def distribute_and_execute(self, target_files: List[str], test_cmd: str) -> dict:
        """
        Distribui a carga de trabalho de múltiplos arquivos para abelhas operárias
        independentes e executa os reparos de forma concorrente em paralelo.
        """
        logger.info(f"RAINHA | Iniciando orquestração da Colmeia para {len(target_files)} arquivos alvos.")
        print("\n======================================================================")
        print("🐝 ORQUESTRADOR DA COLMEIA MEA (ABELHA RAINHA) ATIVO")
        print("======================================================================")
        print(f"[+] Nodos Operários Alvos: {target_files}")
        print(f"[+] Comando de Teste Global: {test_cmd}")
        print("----------------------------------------------------------------------\n")

        # 1. Checagem de Vitalidade Soberana no nível da Rainha antes de disparar os operários
        if not self.gate.check_vitality():
            logger.critical("RAINHA | Execução abortada: Oráculo de Vitalidade bloqueado.")
            print("[-] [RAINHA] Conexão remota de vitalidade bloqueada. Abortando enxame.")
            return {}

        # Importação tardia do execute_hunter_loop para evitar imports circulares no pacote
        from core import execute_hunter_loop

        resultados_colmeia = {}

        # 2. Gerenciador de Execução Concorrente (ThreadPoolExecutor)
        # Cria uma thread dedicada para cada abelha operária trabalhar em paralelo
        max_trabalhadores = min(len(target_files), os.cpu_count() or 4)
        logger.info(f"RAINHA | Despachando {max_trabalhadores} threads operárias concorrentes.")

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_trabalhadores) as executor:
            # Mapeia cada chamada do execute_hunter_loop ao seu respectivo arquivo alvo
            tarefas_futuras = {
                executor.submit(execute_hunter_loop, filepath, test_cmd, self.master_key): filepath
                for filepath in target_files
            }

            # Aguarda e coleta a finalização de cada nodo conforme eles concluem
            for futura in concurrent.futures.as_completed(tarefas_futuras):
                filepath = tarefas_futuras[futura]
                try:
                    # Se o Hunter-Loop do arquivo terminar sem exceções unhandled, considera sucesso
                    futura.result()
                    resultados_colmeia[filepath] = "RESOLVIDO COM SUCESSO"
                    logger.info(f"RAINHA | Nodo {filepath} concluído com sucesso.")
                    print(f"[🎉] [RAINHA] Abelha Operária do arquivo '{filepath}' concluiu o reparo.")
                except Exception as e:
                    resultados_colmeia[filepath] = f"FALHOU: {e}"
                    logger.error(f"RAINHA | Falha crítica no Nodo {filepath}: {e}")
                    print(f"[-] [RAINHA] Erro crítico na Abelha Operária do arquivo '{filepath}': {e}")

        # 3. Emissão de Relatório Consolidado de Unificação da Colmeia
        print("\n======================================================================")
        print("📊 RELATÓRIO DE CONSOLIDAÇÃO DA COLMEIA (SWARM RESOLUTION)")
        print("======================================================================")
        for arquivo, status in resultados_colmeia.items():
            print(f" 📍 Arquivo: {arquivo:<30} ──► Status: {status}")
        print("======================================================================\n")

        logger.info("RAINHA | Orquestração e consolidação de tarefas concluídas.")
        return resultados_colmeia
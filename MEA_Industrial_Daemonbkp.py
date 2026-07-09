# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.4 — SOVEREIGN INDUSTRIAL TELEMETRY DAEMON (Calibrated Equilibrium)
#  Copyright (c) 2026 Bruno Loureiro Desidera. All rights reserved.
# ==============================================================================
import os
import sys
import json
import time
import subprocess
from datetime import datetime

CUSTO_INPUT_1M_USD = 0.150
CUSTO_OUTPUT_1M_USD = 0.600

def load_env_manually():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

load_env_manually()

def aplicar_fisica_sobrecarga(porto):
    """
    Física Térmica Calibrada para Equilíbrio Dinâmico:
    - Aquecimento controlado por contêiner: +2.0°C por ciclo.
    - Resfriamento por manutenção acelerado: -10.0°C por ciclo.
    - Limiar de reativação facilitado: < 55.0°C.
    """
    for g in porto["guindastes"]:
        carga = len(g["fila_cargas"])
        if g["status"] == "ATIVO" or g["status"] == "ALERTA_TEMPERATURA":
            # Aquecimento suave baseado na carga
            g["temperatura_motor"] += float(carga * 2.0)
            # Resfriamento operacional padrão
            g["temperatura_motor"] -= 1.0
        elif g["status"] == "EM_MANUTENCAO" or g["status"] == "FALHA_MECANICA":
            # Resfriamento rápido em manutenção (Ventilação forçada ativa)
            g["temperatura_motor"] = max(25.0, g["temperatura_motor"] - 10.0)
            
            # Protocolo Auto-Healing: Reativa a máquina se ela esfriar abaixo de 55°C
            if g["status"] == "EM_MANUTENCAO" and g["temperatura_motor"] < 55.0:
                g["status"] = "ATIVO"
                print(f"\n[🌱] [AUTO-HEALING] {g['id']} esfriou para {g['temperatura_motor']:.1f}°C. Reativado para operação!")

        # Atualização de estados com base nos limites de temperatura
        if g["temperatura_motor"] > 95.0 and g["status"] != "FALHA_MECANICA":
            print(f"\n[🚨] [ESTOURO_TÉRMICO] Motor de {g['id']} superaqueceu a {g['temperatura_motor']:.1f}°C! Fusível derretido.")
            g["status"] = "FALHA_MECANICA"
            g["fila_cargas"] = [] 
        elif g["temperatura_motor"] > 80.0 and g["status"] == "ATIVO":
            g["status"] = "ALERTA_TEMPERATURA"
        elif g["temperatura_motor"] <= 80.0 and g["status"] == "ALERTA_TEMPERATURA":
            g["status"] = "ATIVO"

def execute_sre_operational_loop():
    porto_path = "porto_telemetria.json"
    decisao_path = "decisao_porto.json"

    if not os.path.exists(porto_path):
        print("[-] Erro: Arquivo porto_telemetria.json não encontrado.")
        return False

    with open(porto_path, "r") as f:
        porto = json.load(f)

    # 1. Aplica a física antes de tomar a decisão (O tempo passa)
    porto["tempo_rodada"] += 1
    aplicar_fisica_sobrecarga(porto)
    
    print(f"\n================ [RODADA DE ANÁLISE: {porto['tempo_rodada']}] ================")
    print(f"Status do pátio: {porto['status_global']}")
    for g in porto["guindastes"]:
        print(f"  ↳ {g['id']}: Status: {g['status']} | Temp: {g['temperatura_motor']:.1f}°C | Fila: {g['fila_cargas']}")

    # Verifica se o porto entrou em colapso total
    ativos = [g for g in porto["guindastes"] if g["status"] in ["ATIVO", "ALERTA_TEMPERATURA"]]
    if not list(ativos):
        porto["status_global"] = "SISTEMA_COLAPSADO_PARALISAÇÃO_TOTAL"
        with open(porto_path, "w") as f: json.dump(porto, f, indent=4)
        print("\n[💀] [CRITICAL_FAIL] Todos os guindastes falharam! Linha de produção parou de vez.")
        return False

    # 2. Inicializa decisão temporária
    with open(decisao_path, "w") as f:
        f.write("# PENDING DECISION")

    # INSTRUÇÃO DE CONTROLE PREDITIVO E ALOCAÇÃO DE RISCO (SRE v10.7)
    ISSUE_STMT = f"""
    ROLE: You are the Autonomous Port Operations Director specializing in Predictive SRE.
    Goal: Prevent thermal shutdown (failure if temperature > 95°C) and manage cargo.
    
    CURRENT STATE:
    {json.dumps(porto, indent=2)}
    
    PREDICTIVE MAINTENANCE RULES:
    1. Gantry_3 is in 'FALHA_MECANICA'. Move its cargo to active gantries immediately.
    2. Monitor temperatures closely! If any active Gantry's temperature is above 80.0°C, it is in 'ALERTA_TEMPERATURA'.
    3. To prevent a catastrophic thermal shutdown (>95°C), you MUST proactively trigger "MAINTENANCE" for any Gantry in 'ALERTA_TEMPERATURA'.
    4. When putting a Gantry in "MAINTENANCE":
       - Set its action inside 'gantry_actions' to "MAINTENANCE" (e.g., "Gantry_1": "MAINTENANCE"). This clears its queue and allows it to cool down.
       - You MUST redistribute all of its current 'fila_cargas' to the other active Gantry.
    5. Balance the remaining loads so no active Gantry exceeds 80°C.
    6. Respond strictly in JSON using the schema below. Do not write markdown.
    
    REPLACE the content of 'decisao_operacional.json' with your solution.
    
    <<<<<<< SEARCH
    # PENDING DECISION
    =======
    {{
      "action": "THROTTLE" | "REDISTRIBUTE" | "HOLD",
      "gantry_actions": {{
         "Gantry_1": "MAINTENANCE",
         "Gantry_2": ["Container_A1", "Container_B1", "Container_C1", "Container_C2", "Container_C3"]
      }},
      "reasoning": "Explain your thermal management strategy."
    }}
    >>>>>>> REPLACE
    """

    test_cmd = f'powershell -Command "if (Get-Content {decisao_path} | Select-String \'PENDING\') {{ exit 1 }} else {{ exit 0 }}"'
    env_config = os.environ.copy()
    env_config["PYTHONIOENCODING"] = "utf-8"
    env_config["MEA_BENCHMARK"] = "true"

    # IA Toma a decisão
    subprocess.run([sys.executable, "core.py", decisao_path, test_cmd, ISSUE_STMT], env=env_config, stdout=subprocess.DEVNULL)

    # 3. Processa a decisão
    if os.path.exists(decisao_path):
        try:
            with open(decisao_path, "r") as f:
                decisao_data = json.load(f)
            
            action = decisao_data.get("action", "HOLD").upper()
            g_actions = decisao_data.get("gantry_actions", {})
            reasoning = decisao_data.get("reasoning", "No explanation.")

            print(f"\n[+] DECISÃO DA MEA: {action}")
            print(f"    ↳ Raciocínio Preditivo SRE: {reasoning}")

            # --- EXECUÇÃO FÍSICA CORRIGIDA (SRE LOOP DINÂMICO) ---
            if action in ["REDISTRIBUTE", "THROTTLE", "HOLD"]:
                for g in porto["guindastes"]:
                    g_id = g["id"]
                    
                    # 1. Se a IA enviou o guindaste para MANUTENÇÃO, altera estado e limpa fila
                    if g_actions.get(g_id) == "MAINTENANCE" and g["status"] != "FALHA_MECANICA":
                        g["status"] = "EM_MANUTENCAO"
                        g["fila_cargas"] = []
                        print(f"    ↳ [CONTROLE] {g_id} movido para MANUTENÇÃO preventiva para resfriamento.")
                    
                    # 2. Se a IA definiu uma nova alocação e o guindaste está apto, sobrescrevemos a fila
                    elif g_id in g_actions and isinstance(g_actions[g_id], list):
                        if g["status"] not in ["FALHA_MECANICA", "EM_MANUTENCAO"]:
                            g["fila_cargas"] = g_actions[g_id]
                            print(f"    ↳ [CONTROLE] Fila do {g_id} atualizada: {g['fila_cargas']}")

                # Força o Gantry_3 (originalmente quebrado) a manter fila vazia para consistência
                for g in porto["guindastes"]:
                    if g["id"] == "Gantry_3" and g["status"] == "FALHA_MECANICA":
                        g["fila_cargas"] = []

                porto["status_global"] = "ESTÁVEL (AUTO-RECUPERADO)" if action != "HOLD" else "OPERANDO"

            # Salva o log do ciclo
            log_entrada = {
                "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ciclo": porto["tempo_rodada"],
                "decisao": action,
                "raciocinio": reasoning
            }
            porto["registro_operacional"].append(log_entrada)

            with open(porto_path, "w") as f:
                json.dump(porto, f, indent=4)

        except Exception as e:
            print(f"[-] Erro de processamento operacional: {e}")
        finally:
            if os.path.exists(decisao_path): os.remove(decisao_path)
            if os.path.exists(decisao_path + ".bak"): os.remove(decisao_path + ".bak")
    
    return True

def main_loop():
    print("[*] Iniciando Simulador de Telemetria Termo-Física Portuária.")
    
    # Rodaremos 5 ciclos seguidos para ver o balanceamento térmico ativo!
    for i in range(5):
        alive = execute_sre_operational_loop()
        if not alive:
            break
        print("[~] Aguardando 5 segundos para o próximo ciclo de telemetria...")
        time.sleep(5)

if __name__ == "__main__":
    main_loop()
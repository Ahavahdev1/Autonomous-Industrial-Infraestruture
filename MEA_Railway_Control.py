# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.4 — SOVEREIGN RAILWAY TRAFFIC DISPATCHER (SRE Simulation)
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

def run_railway_simulation():
    print("======================================================================")
    print("🚦 MEA v10.6.4 'AGIR' - SIMULADOR DE SINALIZAÇÃO FERROVIÁRIA SOBERANA")
    print("======================================================================\n")

    trilhos_path = "trilhos_estado.json"
    decisao_path = "decisao_sinalizador.json"

    if not os.path.exists(trilhos_path):
        print("[-] Erro: Arquivo trilhos_estado.json não encontrado.")
        return

    with open(trilhos_path, "r", encoding="utf-8") as f:
        trilhos = json.load(f)

    print(f"[+] Status da Malha: {trilhos['status_malha']}")
    print(f"[🚨] OBSTÁCULO DETECTADO: {trilhos['obstaculos'][0]['tipo']} na {trilhos['obstaculos'][0]['linha']}!")
    print(f"    ↳ {trilhos['trens'][0]['id']} está a {trilhos['trens'][0]['distancia_obstaculo_m']} metros da colisão a {trilhos['trens'][0]['velocidade_kmh']} km/h.\n")

    # Inicializa o cofre de decisão temporário
    with open(decisao_path, "w", encoding="utf-8") as f:
        f.write("# PENDING DECISION")

    # ORDEM DE DESPACHO CRÍTICO
    ISSUE_STMT = f"""
    ROLE: You are the Sovereign Railway Signaling Director.
    Emergency: Train_1 is heading towards an obstacle on Line_A.
    
    CURRENT STATE:
    {json.dumps(trilhos, indent=2)}
    
    MISSION:
    1. Alter the signal states ('VERDE', 'VERMELHO') to prevent collision.
    2. Route Train_1 to the empty and safe track 'Linha_C'.
    3. Ensure Train_2 on Line_B slows down or holds if there is junction risk.
    4. Generate the response strictly in JSON.
    
    REPLACE the content of 'decisao_sinalizador.json' with your solution.
    
    <<<<<<< SEARCH
    # PENDING DECISION
    =======
    {{
      "status_malha": "RE-ROUTED_AND_SAFE",
      "signal_changes": {{
        "Signal_A": "VERMELHO",
        "Signal_B": "VERMELHO",
        "Signal_C": "VERDE"
      }},
      "train_routing": {{
        "Trem_1_Mercadorias": "Linha_C"
      }},
      "reasoning": "Closed Signal_A to stop any other entry. Opened Signal_C to divert Train_1 safely away from maintenance block. Temporarily closed Signal_B to avoid junction collision."
    }}
    >>>>>>> REPLACE

    CRITICAL: Respond ONLY with the JSON block. Do not write markdown.
    """

    test_cmd = f'powershell -Command "if (Get-Content {decisao_path} | Select-String \'PENDING\') {{ exit 1 }} else {{ exit 0 }}"'

    env_config = os.environ.copy()
    env_config["PYTHONIOENCODING"] = "utf-8"
    env_config["MEA_BENCHMARK"] = "true"

    print("[🚀] DISPARANDO COGNIÇÃO FERROVIÁRIA DA MEA EM MILISSEGUNDOS...")
    subprocess.run([sys.executable, "core.py", decisao_path, test_cmd, ISSUE_STMT], env=env_config)

    if os.path.exists(decisao_path):
        try:
            with open(decisao_path, "r", encoding="utf-8") as f:
                decisao_data = json.load(f)
            
            status_malha = decisao_data.get("status_malha", "EMERGENCY")
            signals = decisao_data.get("signal_changes", {})
            routing = decisao_data.get("train_routing", {})
            reasoning = decisao_data.get("reasoning", "No explanation.")

            print(f"\n[+] RESOLUÇÃO DA MEA COLETADA: {status_malha}")
            print(f"    ↳ Raciocínio de Engenharia: {reasoning}")

            # Execução Física e Validação Matemática no Python
            # Impede que dois trens ocupem a mesma linha na nova rota
            colisao_prevent = True
            for train_id, target_line in routing.items():
                for t in trilhos["trens"]:
                    if t["id"] != train_id and t["linha_atual"] == target_line:
                        print(f"[🚨] [GUARDRAIL] COLISÃO DETECTADA NO DESVIO! {t['id']} já está na {target_line}. Abortando desvio!")
                        colisao_prevent = False
                        break

            if colisao_prevent:
                # Aplica as alterações no banco de dados físico de forma determinística
                trilhos["status_malha"] = status_malha
                
                # Altera os semáforos físicos
                for sig in trilhos["sinalizadores"]:
                    if sig["id"] in signals:
                        sig["status"] = signals[sig["id"]]

                # Altera a rota física do trem
                for train_id, target_line in routing.items():
                    for t in trilhos["trens"]:
                        if t["id"] == train_id:
                            t["linha_atual"] = target_line
                            t["distancia_obstaculo_m"] = 99999 # Longe do perigo agora

                # Grava histórico
                novo_log = {
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "evento": "Divergência Crítica de Tráfego Resolvida",
                    "diagnostico": reasoning
                }
                trilhos["registro_incidentes"] = trilhos.get("registro_incidentes", []) + [novo_log]

                with open(trilhos_path, "w", encoding="utf-8") as f:
                    json.dump(trilhos, f, indent=4)

                print("\n[+] [SRE-TRAFFIC-ENGINE] Banco de dados dos sinalizadores atualizado.")
                print("[+] Semáforos físicos alterados e rotas dos trens isoladas com sucesso!")

        except Exception as e:
            print(f"[-] Erro ao processar controle ferroviário: {e}")
        finally:
            if os.path.exists(decisao_path): os.remove(decisao_path)
            if os.path.exists(decisao_path + ".bak"): os.remove(decisao_path + ".bak")

if __name__ == "__main__":
    run_railway_simulation()    
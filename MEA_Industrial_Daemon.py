# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.5 — INDUSTRIAL DAEMON WITH DYNAMIC TOOL SYNTHESIS (Immune Version)
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
    """Simula aquecimento realista baseado na carga atual."""
    for g in porto["guindastes"]:
        carga = len(g["fila_cargas"])
        if g["status"] in ["ATIVO", "ALERTA_TEMPERATURA"]:
            g["temperatura_motor"] += float(carga * 2.0)
            g["temperatura_motor"] -= 1.0 # Resfriamento operacional passivo
        elif g["status"] in ["EM_MANUTENCAO", "FALHA_MECANICA"]:
            g["temperatura_motor"] = max(25.0, g["temperatura_motor"] - 10.0)
            # Reativa se resfriar
            if g["status"] == "EM_MANUTENCAO" and g["temperatura_motor"] < 50.0:
                g["status"] = "ATIVO"
                print(f"[🌱] [SRE] {g['id']} resfriou com sucesso. Reativado para operação!")

        # Limites térmicos
        if g["temperatura_motor"] > 95.0 and g["status"] != "FALHA_MECANICA":
            print(f"[🚨] [ESTOURO_TÉRMICO] Motor de {g['id']} superaqueceu ({g['temperatura_motor']:.1f}°C)!")
            g["status"] = "FALHA_MECANICA"
            g["fila_cargas"] = []
        elif g["temperatura_motor"] > 80.0 and g["status"] == "ATIVO":
            g["status"] = "ALERTA_TEMPERATURA"
        elif g["temperatura_motor"] <= 80.0 and g["status"] == "ALERTA_TEMPERATURA":
            g["status"] = "ATIVO"

def run_sre_synthesis_loop():
    porto_path = "porto_telemetria.json"
    otimizador_path = "otimizador_patio.py"

    if not os.path.exists(porto_path):
        print("[-] Erro: Arquivo porto_telemetria.json não encontrado.")
        return False

    # AJUSTE SÊNIOR: Lemos com utf-8-sig para tolerar a marcação BOM do Windows
    with open(porto_path, "r", encoding="utf-8-sig") as f:
        porto = json.load(f)

    # 1. Aplica a física antes de tomar a decisão (O tempo passa)
    porto["tempo_rodada"] += 1
    aplicar_fisica_sobrecarga(porto)
    
    print(f"\n================ [RODADA DE ANÁLISE: {porto['tempo_rodada']}] ================")
    print(f"Status do pátio: {porto['status_global']}")
    for g in porto["guindastes"]:
        print(f"  ↳ {g['id']}: Status: {g['status']} | Temp: {g['temperatura_motor']:.1f}°C | Fila: {g['fila_cargas']}")

    # Salva as alterações térmicas em disco imediatamente em UTF-8 puro (sem BOM)
    with open(porto_path, "w", encoding="utf-8") as f:
        json.dump(porto, f, indent=4)

    # Verifica se o porto entrou em colapso total
    ativos = [g for g in porto["guindastes"] if g["status"] in ["ATIVO", "ALERTA_TEMPERATURA"]]
    if not list(ativos):
        porto["status_global"] = "SISTEMA_COLAPSADO_PARALISAÇÃO_TOTAL"
        with open(porto_path, "w", encoding="utf-8") as f: json.dump(porto, f, indent=4)
        print("\n[💀] [CRITICAL_FAIL] Todos os guindastes falharam! Linha de produção parou de vez.")
        return False

    # 2. Inicializa arquivo da ferramenta vazio
    with open(otimizador_path, "w", encoding="utf-8") as f:
        f.write("# EMPTY OPTIMIZER TOOL")

    # ORDEM DE SÍNTESE DINÂMICA COM VACINA DE CODIFICAÇÃO (Regra 7)
    ISSUE_STMT = f"""
    TASK: Write a Python program 'otimizador_patio.py' to optimize the port gantry queues.
    
    CRITICAL SCHEMA MAP (You MUST use these exact keys in your Python code):
    - The database file 'porto_telemetria.json' uses PORTUGUESE keys.
    - List of gantries is: "guindastes" (DO NOT use "gantries" in your python code!)
    - Gantry ID is: "id"
    - Temperature field is: "temperatura_motor"
    - Queue array is: "fila_cargas"
    - Status field is: "status" ("ATIVO", "ALERTA_TEMPERATURA", "FALHA_MECANICA", "EM_MANUTENCAO")
    
    COMPLIANCE RULES:
    1. Read 'porto_telemetria.json'.
    2. Identify active gantries ('status' is 'ATIVO' or 'ALERTA_TEMPERATURA') and disabled gantries ('FALHA_MECANICA' or 'EM_MANUTENCAO').
    3. Collect all containers from Gantry_3 and any Gantry in 'ALERTA_TEMPERATURA' (temp > 80.0°C).
    4. Move the alerting Gantry to 'EM_MANUTENCAO' and empty its queue.
    5. Move all collected containers to the coolest active Gantry (the one with the lowest 'temperatura_motor' that is below 80°C).
    6. Write the updated data back to 'porto_telemetria.json' in valid JSON format.
    7. CRITICAL COCODING VACCINE: When opening 'porto_telemetria.json' in your python code for reading or writing, you MUST explicitly specify 'encoding="utf-8"' (e.g. open(..., encoding="utf-8")) to prevent character decoding errors on Windows.
    
    Replace the entire file 'otimizador_patio.py'.
    
    <<<<<<< SEARCH
    # EMPTY OPTIMIZER TOOL
    =======
    [Your full Python script using the PORTUGUESE keys "guindastes", "fila_cargas" and correct 'encoding="utf-8"']
    >>>>>>> REPLACE
    
    CRITICAL: Output ONLY valid Python code inside the SEARCH/REPLACE block. No markdown explanations.
    """

    test_cmd = f'powershell -Command "if (Get-Content {otimizador_path} | Select-String \'EMPTY\') {{ exit 1 }} else {{ exit 0 }}"'
    env_config = os.environ.copy()
    env_config["PYTHONIOENCODING"] = "utf-8"
    env_config["MEA_BENCHMARK"] = "true"

    # A MEA vai criar o arquivo otimizador_patio.py
    subprocess.run([sys.executable, "core.py", otimizador_path, test_cmd, ISSUE_STMT], env=env_config, stdout=subprocess.DEVNULL)

    # EXECUÇÃO DA FERRAMENTA SINTETIZADA
    if os.path.exists(otimizador_path) and "EMPTY" not in open(otimizador_path, "r", encoding="utf-8").read():
        print("[⚙️] [TOOL-USE] Executando o Otimizador de Pátio gerado pela MEA...")
        try:
            subprocess.run([sys.executable, otimizador_path], check=True)
            print("[+] [TOOL-USE] Otimização matemática aplicada ao banco de dados com sucesso!")
        except Exception as e:
            print(f"[-] [SRE-BLOCK] A ferramenta sintetizada pela IA falhou na execução: {e}")
        finally:
            if os.path.exists(otimizador_path): os.remove(otimizador_path)
            if os.path.exists(otimizador_path + ".bak"): os.remove(otimizador_path + ".bak")

    # Salva o estado atualizado do porto na rodada (Lemos com utf-8-sig)
    with open(porto_path, "r", encoding="utf-8-sig") as f:
        porto = json.load(f)
    
    log_entrada = {
        "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "ciclo": porto["tempo_rodada"],
        "evento": "Otimização Sintética de Tráfego Executada"
    }
    porto["registro_operacional"] = porto.get("registro_operacional", []) + [log_entrada]
    with open(porto_path, "w", encoding="utf-8") as f: json.dump(porto, f, indent=4)

    return True

def main():
    print("[*] Iniciando Simulador de Automação com Síntese Dinâmica de Código.")
    for i in range(5):
        alive = run_sre_synthesis_loop()
        if not alive: break
        time.sleep(5)

if __name__ == "__main__":
    main()
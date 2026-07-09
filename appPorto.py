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
import codecs
from datetime import datetime

# --- SOLUÇÃO DE BLINDAGEM DE CODIFICAÇÃO ---
# Força o sistema a substituir emojis/caracteres inválidos por '?' em vez de crashar
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach(), errors='replace')
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach(), errors='replace')

# --- LOGGING AUTOMÁTICO PARA DASHBOARD ---
class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open("app.log", "a", encoding="utf-8")
    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)
        self.log.flush()
    def flush(self):
        self.terminal.flush()
        self.log.flush()

sys.stdout = Logger()
sys.stderr = Logger()

# --- CONFIGURAÇÃO ---
def load_env_manually():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

load_env_manually()

def aplicar_fisica_sobrecarga(porto):
    for g in porto["guindastes"]:
        carga = len(g["fila_cargas"])
        if g["status"] in ["ATIVO", "ALERTA_TEMPERATURA"]:
            g["temperatura_motor"] += float(carga * 2.0)
            g["temperatura_motor"] -= 1.0 
        elif g["status"] in ["EM_MANUTENCAO", "FALHA_MECANICA"]:
            g["temperatura_motor"] = max(25.0, g["temperatura_motor"] - 10.0)
            if g["status"] == "EM_MANUTENCAO" and g["temperatura_motor"] < 50.0:
                g["status"] = "ATIVO"
                print(f"[INFO] [SRE] {g['id']} resfriou com sucesso.")

        if g["temperatura_motor"] > 95.0 and g["status"] != "FALHA_MECANICA":
            print(f"[ALERT] [THERMAL_OVERFLOW] {g['id']} superaqueceu ({g['temperatura_motor']:.1f}C)!")
            g["status"] = "FALHA_MECANICA"
            g["fila_cargas"] = []
        elif g["temperatura_motor"] > 80.0 and g["status"] == "ATIVO":
            g["status"] = "ALERTA_TEMPERATURA"
        elif g["temperatura_motor"] <= 80.0 and g["status"] == "ALERTA_TEMPERATURA":
            g["status"] = "ATIVO"

def executar_otimizador_seguro(caminho_script, timeout_segundos=2.0):
    try:
        resultado = subprocess.run([sys.executable, caminho_script], capture_output=True, text=True, timeout=timeout_segundos)
        return resultado.returncode == 0
    except Exception as e:
        print(f"[WARN] [SRE-BLOCK] Erro: {e}")
        return False

def run_sre_synthesis_loop():
    porto_path = "porto_telemetria.json"
    otimizador_path = "otimizador_patio.py"

    if not os.path.exists(porto_path): return False
    with open(porto_path, "r", encoding="utf-8-sig") as f: porto = json.load(f)

    porto["tempo_rodada"] += 1
    aplicar_fisica_sobrecarga(porto)
    
    print(f"\n================ [RODADA: {porto['tempo_rodada']}] ================")
    with open(porto_path, "w", encoding="utf-8") as f: json.dump(porto, f, indent=4)

    with open(otimizador_path, "w", encoding="utf-8") as f: f.write("# EMPTY OPTIMIZER TOOL")

    ISSUE_STMT = "TASK: Optimize port queues. Keys: 'guindastes', 'id', 'temperatura_motor', 'fila_cargas', 'status'."
    
    # Executa o core.py com proteção extra
    subprocess.run([sys.executable, "core.py", otimizador_path, "test", ISSUE_STMT], stdout=subprocess.DEVNULL)

    if os.path.exists(otimizador_path) and "EMPTY" not in open(otimizador_path, "r", encoding="utf-8").read():
        executar_otimizador_seguro(otimizador_path)
        try: os.remove(otimizador_path)
        except: pass

    return True

def main():
    print("[*] Iniciando MEA Daemon v10.6.5 (Logging & Codificação Protegidos)")
    for i in range(50):
        if not run_sre_synthesis_loop(): break
        time.sleep(5)

if __name__ == "__main__":
    main()
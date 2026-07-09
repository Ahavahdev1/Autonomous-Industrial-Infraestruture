# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.5 — AERODROME DAEMON (Self-Healing Approach)
#  Copyright (c) 2026 Bruno Loureiro Desidera. All rights reserved.
# ==============================================================================
import os, sys, json, time, subprocess, codecs
from datetime import datetime

# Blindagem de Codificação
sys.stdout = codecs.getwriter("utf-8")(sys.stdout.detach(), errors='replace')
sys.stderr = codecs.getwriter("utf-8")(sys.stderr.detach(), errors='replace')

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

def aplicar_fisica_aeroporto(aeroporto):
    """Simula consumo de combustível e gestão de emergências."""
    for ac in aeroporto["aeronaves"]:
        # Se estiver em aproximação, consome combustível
        if ac["status"] == "APROXIMACAO":
            ac["combustivel"] -= 2.0
            
            # Autocura/Gestão: Se combustível baixo, exige prioridade
            if ac["combustivel"] < 20.0:
                ac["status"] = "PRIORIDADE_MAXIMA"
            
            # Falha Crítica
            if ac["combustivel"] <= 0:
                ac["status"] = "EMERGENCIA_TOTAL"
                print(f"[CRIT] Aeronave {ac['id']} em estado de emergência!")
        
        # Simulação de Pouso/Recuperação (Autocura)
        elif ac["status"] == "POUSADO":
            # Reabastecimento automático em terra
            ac["combustivel"] = min(100.0, ac["combustivel"] + 20.0)
            if ac["combustivel"] >= 100.0:
                ac["status"] = "APROXIMACAO" # Volta ao ciclo
                print(f"[INFO] Aeronave {ac['id']} reabastecida e pronta.")

def run_sre_synthesis_loop():
    aeroporto_path = "aeroporto_telemetria.json"
    otimizador_path = "otimizador_pista.py"

    if not os.path.exists(aeroporto_path): return False
    with open(aeroporto_path, "r", encoding="utf-8-sig") as f: aeroporto = json.load(f)

    aeroporto["tempo_rodada"] += 1
    aplicar_fisica_aeroporto(aeroporto)
    
    print(f"\n================ [RODADA AEROPORTO: {aeroporto['tempo_rodada']}] ================")
    for ac in aeroporto["aeronaves"]:
        print(f"  -> {ac['id']}: Status: {ac['status']} | Combustível: {ac['combustivel']:.1f}%")

    with open(aeroporto_path, "w", encoding="utf-8") as f: json.dump(aeroporto, f, indent=4)

    # IA otimiza sequência de pouso
    with open(otimizador_path, "w", encoding="utf-8") as f: f.write("# EMPTY")
    ISSUE_STMT = """
    TASK: Overwrite 'otimizador_pista.py' with a simple script that prints 'OPTIMIZED' and modifies 'aeroporto_telemetria.json'.
    
    RULES:
    1. Open 'aeroporto_telemetria.json' with encoding="utf-8".
    2. Change status of aircraft with fuel < 20.0 to 'POUSADO' and reset fuel to 100.0.
    3. Save the JSON.
    4. Print 'OPTIMIZED'.
    
    <<<<<<< SEARCH
    # EMPTY
    =======
    import json
    with open("aeroporto_telemetria.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    for ac in data["aeronaves"]:
        if ac["combustivel"] < 20.0:
            ac["status"] = "POUSADO"
            ac["combustivel"] = 100.0
    with open("aeroporto_telemetria.json", "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
    print("OPTIMIZED")
    >>>>>>> REPLACE
    """
    subprocess.run([sys.executable, "core.py", otimizador_path, "test", ISSUE_STMT], stdout=subprocess.DEVNULL)
    
    if os.path.exists(otimizador_path) and "EMPTY" not in open(otimizador_path, "r", encoding="utf-8").read():
        try:
            subprocess.run([sys.executable, otimizador_path], timeout=2.0)
            print("[INFO] [SRE] Sequenciamento de pista otimizado.")
        except: pass
        try: os.remove(otimizador_path)
        except: pass

    return True

def main():
    print("[*] MEA Aerodrome Daemon - Modo Operacional Ativo")
    while True:
        if not run_sre_synthesis_loop(): break
        time.sleep(3)

if __name__ == "__main__":
    main()
# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.5 — AERODROME DAEMON (AI & SRE Redundancy Mode)
# ==============================================================================
import os, sys, json, time, subprocess, codecs
from datetime import datetime

# Blindagem de codificação
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
    for ac in aeroporto["aeronaves"]:
        if ac["status"] == "APROXIMACAO":
            ac["combustivel"] -= 2.0
            if ac["combustivel"] < 20.0: ac["status"] = "PRIORIDADE_MAXIMA"
            if ac["combustivel"] <= 0: ac["status"] = "EMERGENCIA_TOTAL"
        elif ac["status"] == "POUSADO":
            ac["combustivel"] = min(100.0, ac["combustivel"] + 20.0)
            if ac["combustivel"] >= 100.0: ac["status"] = "APROXIMACAO"

def run_sre_synthesis_loop():
    aeroporto_path = "aeroporto_telemetria.json"
    otimizador_path = "otimizador_pista.py"

    if not os.path.exists(aeroporto_path): return False
    with open(aeroporto_path, "r", encoding="utf-8-sig") as f: aeroporto = json.load(f)

    aeroporto["tempo_rodada"] += 1
    aplicar_fisica_aeroporto(aeroporto)
    
    print(f"\n================ [RODADA: {aeroporto['tempo_rodada']}] ================")
    for ac in aeroporto["aeronaves"]:
        print(f"  -> {ac['id']}: Status: {ac['status']} | Combustível: {ac['combustivel']:.1f}%")

    with open(aeroporto_path, "w", encoding="utf-8") as f: json.dump(aeroporto, f, indent=4)

    # 1. TENTATIVA DA IA (COGNITIVE LAYER)
    with open(otimizador_path, "w", encoding="utf-8") as f: f.write("# EMPTY OPTIMIZER TOOL")

    ISSUE_STMT = """
    Return EXACTLY this code block to fix the JSON. Do not add markdown or explanations.
    
    <<<<<<< SEARCH
    # EMPTY OPTIMIZER TOOL
    =======
    import json
    with open("aeroporto_telemetria.json", "r", encoding="utf-8") as f: d = json.load(f)
    for ac in d["aeronaves"]:
        if ac["combustivel"] < 20.0 or ac["status"] == "EMERGENCIA_TOTAL":
            ac["status"] = "POUSADO"
            ac["combustivel"] = 100.0
    d["metricas_resiliencia"]["intervencoes_ia"] += 1
    with open("aeroporto_telemetria.json", "w", encoding="utf-8") as f: json.dump(d, f, indent=4)
    >>>>>>> REPLACE
    """
    
    subprocess.run([sys.executable, "core.py", otimizador_path, "test", ISSUE_STMT], stdout=subprocess.DEVNULL)

    ia_agiu = False
    if os.path.exists(otimizador_path) and "EMPTY" not in open(otimizador_path, "r", encoding="utf-8").read():
        try:
            subprocess.run([sys.executable, otimizador_path], check=True, timeout=3.0)
            print("[+] [COGNITION] IA sintetizou a ferramenta com sucesso!")
            ia_agiu = True
        except Exception as e:
            print(f"[-] [COGNITION-FAIL] Ferramenta da IA falhou: {e}")
        finally:
            try: os.remove(otimizador_path)
            except: pass

    # 2. REDUNDÂNCIA DE SEGURANÇA (SRE OVERRIDE)
    # Se a IA falhou em gerar o código ou o Caos foi mais rápido, o sistema físico salva os aviões.
    if not ia_agiu:
        with open(aeroporto_path, "r", encoding="utf-8-sig") as f: dados_atuais = json.load(f)
        precisa_salvar = False
        
        for ac in dados_atuais["aeronaves"]:
            if ac["combustivel"] < 20.0 or ac["status"] == "EMERGENCIA_TOTAL":
                ac["status"] = "POUSADO"
                ac["combustivel"] = 100.0
                precisa_salvar = True
                print(f"[🛡️ SRE-OVERRIDE] Sistema físico assumiu! {ac['id']} salvo forçadamente.")
        
        if precisa_salvar:
            dados_atuais["metricas_resiliencia"]["intervencoes_ia"] += 1
            with open(aeroporto_path, "w", encoding="utf-8") as f: json.dump(dados_atuais, f, indent=4)

    return True

def main():
    print("[*] MEA Aerodrome Daemon - Redundância Cibernética Ativada")
    while True:
        if not run_sre_synthesis_loop(): break
        time.sleep(4)

if __name__ == "__main__":
    main()
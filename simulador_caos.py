import json
import time
import random
import os

def inject_chaos():
    path = "aeroporto_telemetria.json"
    
    if not os.path.exists(path):
        print("[CAOS] Arquivo de telemetria não encontrado...")
        return

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Probabilidade de 40% de causar uma anomalia em cada ciclo
        if random.random() < 0.4:
            ac = random.choice(data["aeronaves"])
            
            # Escolhe um tipo de falha
            falha = random.choice(["COMBUSTIVEL", "STATUS"])
            
            if falha == "COMBUSTIVEL":
                # Reduz combustível drasticamente
                ac["combustivel"] = max(0, ac["combustivel"] - 35.0)
                print(f"[CAOS] Vazamento de combustível simulado em {ac['id']}!")
            else:
                # Força estado de emergência
                ac["status"] = "EMERGENCIA_TOTAL"
                print(f"[CAOS] Falha técnica simulada em {ac['id']}!")
            
            # Registra a anomalia cientificamente
            data["metricas_resiliencia"]["eventos_de_caos"] += 1
            
            # Salva o estado caótico
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        
    except Exception as e:
        print(f"[CAOS] Erro ao injetar caos: {e}")

print("[*] Iniciando Adversário de Caos (Estudo Científico)")
print("[*] Injetando anomalias a cada 8 segundos...")

while True:
    inject_chaos()
    time.sleep(8)
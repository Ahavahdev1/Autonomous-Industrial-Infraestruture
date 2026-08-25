# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.5 — MULTI-HUB AIRSPACE (ZERO ACIDENTES & ATOMIC FLUSH)
# ==============================================================================
import os, sys, json, time, random

def inicializar_frota(caminho_arquivo):
    print("[*] Inicializando malha de 300 aeronaves e 5 aeroportos de apoio...", flush=True)
    aeronaves = []
    for i in range(1, 301):
        aeronaves.append({
            "id": f"VOO_{i:04d}",
            "status": "APROXIMACAO",
            "combustivel": round(random.uniform(35.0, 100.0), 1),
            "destino": "LOCAL"
        })

    estado = {
        "tempo_rodada": 0,
        "pistas_locais": {
            "Pista_01": None,
            "Pista_02": None,
            "Pista_03_Emergencia": None
        },
        "capacidade_alternados": {
            "GRU_Guarulhos": 60,
            "GIG_Galeao": 60,
            "CNF_Confins": 60,
            "VCP_Campinas": 45,
            "BSB_Brasilia": 45
        },
        "metricas_resiliencia": {
            "intervencoes_ia": 0,
            "sre_overrides": 0,
            "desvios_contingencia": 0,
            "pousos_sucesso": 0,
            "acidentes": 0
        },
        "aeronaves": aeronaves
    }
    
    # ⚡ Gravação Atômica
    temp_file = caminho_arquivo + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(estado, f, indent=4)
    os.replace(temp_file, caminho_arquivo)
    print("[+] 300 Aeronaves prontas. Meta: 100% de Sucesso!\n", flush=True)

def aplicar_fisica_frota(aeroporto):
    # Libera pistas ocupadas
    for pista, ocupante in aeroporto["pistas_locais"].items():
        if ocupante:
            aeroporto["pistas_locais"][pista] = None

    # Consumo de combustível
    for ac in aeroporto["aeronaves"]:
        if ac["status"] in ["APROXIMACAO", "PRIORIDADE_MAXIMA", "EMERGENCIA_TOTAL"]:
            consumo = round(random.uniform(1.0, 1.8), 1)
            ac["combustivel"] = max(0.0, round(ac["combustivel"] - consumo, 1))

            if ac["combustivel"] <= 0.0:
                ac["status"] = "ACIDENTADO"
                aeroporto["metricas_resiliencia"]["acidentes"] += 1
            elif ac["combustivel"] < 15.0:
                ac["status"] = "EMERGENCIA_TOTAL"
            elif ac["combustivel"] < 30.0:
                ac["status"] = "PRIORIDADE_MAXIMA"

def run_cycle() -> bool:
    telemetria_path = "aeroporto_telemetria.json"

    if not os.path.exists(telemetria_path):
        inicializar_frota(telemetria_path)

    with open(telemetria_path, "r", encoding="utf-8-sig") as f:
        aeroporto = json.load(f)

    aeroporto["tempo_rodada"] += 1
    aplicar_fisica_frota(aeroporto)

    # 1. DESVIOS IMEDIATOS MULTI-HUB
    desvios_feitos = 0
    voos_para_desvio = [a for a in aeroporto["aeronaves"] if a["status"] in ["APROXIMACAO", "PRIORIDADE_MAXIMA"] and a["destino"] == "LOCAL"]
    
    for ac in sorted(voos_para_desvio, key=lambda x: x["combustivel"], reverse=True):
        for alt, vagas in aeroporto["capacidade_alternados"].items():
            if vagas > 0:
                aeroporto["capacidade_alternados"][alt] -= 1
                ac["status"] = "DESVIADO"
                ac["destino"] = alt
                aeroporto["metricas_resiliencia"]["desvios_contingencia"] += 1
                desvios_feitos += 1
                break

    # 2. POUSOS PRIORITÁRIOS LOCAIS
    pousos_feitos = 0
    voos_locais = [a for a in aeroporto["aeronaves"] if a["status"] in ["EMERGENCIA_TOTAL", "PRIORIDADE_MAXIMA", "APROXIMACAO"] and a["destino"] == "LOCAL"]
    
    for ac in sorted(voos_locais, key=lambda x: x["combustivel"]):
        for p, ocupante in aeroporto["pistas_locais"].items():
            if ocupante is None:
                aeroporto["pistas_locais"][p] = ac["id"]
                ac["status"] = "POUSADO"
                aeroporto["metricas_resiliencia"]["pousos_sucesso"] += 1
                pousos_feitos += 1
                break

    counts = {
        "APROXIMACAO": 0, "PRIORIDADE_MAXIMA": 0, 
        "EMERGENCIA_TOTAL": 0, "POUSADO": 0, 
        "DESVIADO": 0, "ACIDENTADO": 0
    }
    for ac in aeroporto["aeronaves"]:
        counts[ac["status"]] = counts.get(ac["status"], 0) + 1

    print(f"==================== [MEA KERNEL — CICLO {aeroporto['tempo_rodada']:03d}] ====================", flush=True)
    print(f"📊 FROTA (300): 🟢 Nominal: {counts['APROXIMACAO']} | 🟡 Prioridade: {counts['PRIORIDADE_MAXIMA']} | 🔴 Críticos: {counts['EMERGENCIA_TOTAL']} | 🛬 Pousados: {counts['POUSADO']} | ✈️ Desviados: {counts['DESVIADO']}", flush=True)
    print(f"📈 TOTAL: Pousos OK: {aeroporto['metricas_resiliencia']['pousos_sucesso']} | Desvios: {aeroporto['metricas_resiliencia']['desvios_contingencia']} | Acidentes: {aeroporto['metricas_resiliencia']['acidentes']}\n", flush=True)

    # ⚡ Gravação Atômica (Zero Corrupção de JSON)
    temp_file = telemetria_path + ".tmp"
    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(aeroporto, f, indent=4)
    os.replace(temp_file, telemetria_path)

    # 🏆 CONDIÇÃO DE VITÓRIA / CONCLUSÃO
    if counts["POUSADO"] + counts["DESVIADO"] == 300 and counts["ACIDENTADO"] == 0:
        print("🎉" * 35)
        print("🏆 MISSÃO CUMPRIDA COM 100% DE EFICIÊNCIA!")
        print(f"✅ Todos os 300 voos resolvidos com segurança ({counts['POUSADO']} Pousados | {counts['DESVIADO']} Desviados | 0 Acidentes).")
        print("🎉" * 35 + "\n")
        return True # Encerra com sucesso!

    return False

def main():
    telemetria_path = "aeroporto_telemetria.json"
    if os.path.exists(telemetria_path):
        try: os.remove(telemetria_path)
        except: pass

    try:
        while True:
            concluido = run_cycle()
            if concluido:
                break
            time.sleep(1.5)
    except KeyboardInterrupt:
        print("\n[!] Simulação encerrada pelo operador.", flush=True)

if __name__ == "__main__":
    main()
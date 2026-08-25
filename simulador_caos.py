# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.5 — CHAOS MONKEY / ADVERSE CONDITIONS INJECTOR
# ==============================================================================
import os, sys, json, time, random

TELEMETRIA_PATH = "aeroporto_telemetria.json"

def carregar_telemetria():
    if not os.path.exists(TELEMETRIA_PATH):
        print("[-] Arquivo aeroporto_telemetria.json não encontrado. O Kernel está rodando?")
        return None
    try:
        with open(TELEMETRIA_PATH, "r", encoding="utf-8-sig") as f:
            return json.load(f)
    except Exception as e:
        return None

def salvar_telemetria(dados):
    try:
        with open(TELEMETRIA_PATH, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4)
        return True
    except:
        return False

# ==============================================================================
# VETORES DE CAOS
# ==============================================================================
def injetar_vazamento_massa(qtd_avioes=35):
    dados = carregar_telemetria()
    if not dados: return
    
    afetados = 0
    candidatos = [ac for ac in dados["aeronaves"] if ac["status"] == "APROXIMACAO"]
    random.shuffle(candidatos)

    for ac in candidatos[:qtd_avioes]:
        ac["combustivel"] = round(random.uniform(5.0, 14.0), 1)
        ac["status"] = "EMERGENCIA_TOTAL"
        afetados += 1

    if salvar_telemetria(dados):
        print(f"\n[💥 CAOS INJETADO] Pane seca súbita injetada em {afetados} aeronaves simultaneamente!")

def fechar_pista_emergencia():
    dados = carregar_telemetria()
    if not dados: return

    pistas = list(dados["pistas_locais"].keys())
    pista_alvo = random.choice(pistas)
    dados["pistas_locais"][pista_alvo] = "OBSTRUCAO_FOGO_CLIMA"

    if salvar_telemetria(dados):
        print(f"\n[🌪️ CAOS INJETADO] {pista_alvo} INTERDITADA por ventos severos/destroços!")

def blecaute_aeroporto_alternado():
    dados = carregar_telemetria()
    if not dados: return

    alternados = list(dados["capacidade_alternados"].keys())
    alvo = random.choice(alternados)
    dados["capacidade_alternados"][alvo] = 0

    if salvar_telemetria(dados):
        print(f"\n[🛑 CAOS INJETADO] {alvo} FECHADO para pousos de contingência!")

def tempestade_perfeita():
    print("\n[🚨🚨🚨 CAOS MÁXIMO] INJETANDO TEMPESTADE CATEGORIA 5 NA MALHA AÉREA...")
    injetar_vazamento_massa(50)
    fechar_pista_emergencia()
    blecaute_aeroporto_alternado()

# ==============================================================================
# MENU / LOOP AUTOMÁTICO DE ESTRESSE
# ==============================================================================
def modo_bombardeio_automatico():
    print("\n[*] INICIANDO PROTOCOLO DE SATURAÇÃO CONTÍNUA...")
    print("[*] Injetando ataques e anomalias a cada 6 segundos...")
    try:
        round_count = 1
        while True:
            print(f"\n--- [ONDA DE CAOS #{round_count}] ---")
            ataque = random.choice([injetar_vazamento_massa, fechar_pista_emergencia, blecaute_aeroporto_alternado])
            ataque()
            round_count += 1
            time.sleep(6)
    except KeyboardInterrupt:
        print("\n[!] Injeção de caos interrompida.")

def menu():
    while True:
        print("\n==================================================")
        print(" 🔥 MEA ADVERSE CONDITIONS INJECTOR (CHAOS MONKEY)")
        print("==================================================")
        print("1. Injetar Vazamento Súbito em 35 Aeronaves")
        print("2. Interditar uma Pista Local (Clima Severo)")
        print("3. Fechar um Aeroporto Alternativo (Blecaute)")
        print("4. TEMPESTADE PERFEITA (Injetar Tudo de Uma Vez)")
        print("5. MODO AUTOMÁTICO (Bombardeio Contínuo de Estresse)")
        print("0. Sair")
        
        escolha = input("\nEscolha o vetor de ataque [0-5]: ").strip()
        
        if escolha == "1": injetar_vazamento_massa()
        elif escolha == "2": fechar_pista_emergencia()
        elif escolha == "3": blecaute_aeroporto_alternado()
        elif escolha == "4": tempestade_perfeita()
        elif escolha == "5": modo_bombardeio_automatico()
        elif escolha == "0": break
        else: print("Opção inválida.")
        time.sleep(1)

if __name__ == "__main__":
    menu()
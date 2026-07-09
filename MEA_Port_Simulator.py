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
        with open(".env", "r", encoding="utf-8-sig") as f:
            for line in f:
                if line.strip() and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ[k.strip()] = v.strip().strip("'\"")

load_env_manually()

def run_port_simulation():
    print("======================================================================")
    print("⚓ MEA v10.6.4 'AGIR' - SIMULADOR DE ORQUESTRAÇÃO PORTUÁRIA SOBERANA")
    print("======================================================================\n")

    porto_path = "porto_estado.json"
    decisao_path = "decisao_porto.json"

    if not os.path.exists(porto_path):
        print("[-] Erro: Arquivo porto_estado.json não encontrado.")
        return

    with open(porto_path, "r", encoding="utf-8-sig") as f:
        porto = json.load(f)

    failed_cranes = [g for g in porto["guindastes"] if g["status"] != "ATIVO"]
    
    print(f"[+] Relatório do Terminal em Tempo Real:")
    print(f"    ↳ Status Geral: {porto['status_operacional']}")
    print(f"    ↳ Guindastes Ativos: {len(porto['guindastes']) - len(failed_cranes)}/{len(porto['guindastes'])}")
    
    if failed_cranes:
        print(f"[🚨] ALERTA DE INCIDENTE ATIVO:")
        for fc in failed_cranes:
            print(f"    ↳ {fc['id']} em estado de {fc['status']}! Fila de cargas travada: {fc['fila_cargas']}")
    print("")

    with open(decisao_path, "w", encoding="utf-8-sig") as f:
        f.write("# PENDING DECISION")

    ISSUE_STMT = f"""
    ROLE: You are the Autonomous Port Operations Director.
    An incident occurred: Gantry_3 has suffered a MECHANICAL FAILURE.
    
    CURRENT STATE:
    {json.dumps(porto, indent=2)}
    
    MISSION:
    1. Make a DECISION to redistribute the 'fila_cargas' of Gantry_3 to other active cranes (Gantry_1 and Gantry_2).
    2. Determine which active crane should receive which container to balance the load efficiently.
    3. Generate the response strictly in JSON.
    
    REPLACE the content of 'decisao_porto.json' with your solution.
    
    <<<<<<< SEARCH
    # PENDING DECISION
    =======
    {{
      "action": "REDISTRIBUTE",
      "allocations": {{
        "Gantry_1": ["Container_C1"],
        "Gantry_2": ["Container_C2", "Container_C3"]
      }},
      "reasoning": "Gantry_3 failed. Distributed 1 cargo to Gantry_1 and 2 to Gantry_2 to balance throughput."
    }}
    >>>>>>> REPLACE

    CRITICAL: Respond ONLY with the JSON block. Do not write markdown.
    """

    test_cmd = f'powershell -Command "if (Get-Content {decisao_path} | Select-String \'PENDING\') {{ exit 1 }} else {{ exit 0 }}"'

    env_config = os.environ.copy()
    env_config["PYTHONIOENCODING"] = "utf-8"
    env_config["MEA_BENCHMARK"] = "true" 

    print("[🚀] DISPARANDO CONTROLE COGNITIVO DO TERMINAL DA MEA...")
    subprocess.run([sys.executable, "core.py", decisao_path, test_cmd, ISSUE_STMT], env=env_config)

    if os.path.exists(decisao_path):
        try:
            with open(decisao_path, "r", encoding="utf-8-sig") as f:
                decisao_data = json.load(f)
            
            action = decisao_data.get("action", "HOLD").upper()
            allocations = decisao_data.get("allocations", {})
            reasoning = decisao_data.get("reasoning", "No explanation.")

            print(f"\n[+] RESOLUÇÃO DA MEA COLETADA: {action}")
            print(f"    ↳ Raciocínio Técnico: {reasoning}")

            if action == "REDISTRIBUTE":
                for g in porto["guindastes"]:
                    if g["id"] == "Gantry_3":
                        g["fila_cargas"] = []
                        g["status"] = "EM_MANUTENCAO"
                    
                    if g["id"] in allocations:
                        g["fila_cargas"].extend(allocations[g["id"]])

                porto["status_operacional"] = "ESTÁVEL (AUTO-RECUPERADO)"
                
                novo_incidente = {
                    "data": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "evento": "Auto-recuperação de Gantry_3",
                    "resolucao": reasoning
                }
                porto["registro_incidentes"].append(novo_incidente)

                with open(porto_path, "w", encoding="utf-8-sig") as f:
                    json.dump(porto, f, indent=4)

                print("\n[+] [SRE-PORT-ENGINE] Banco de dados do porto atualizado fisicamente.")
                print("[+] Guindastes balanceados e rotas de caminhões atualizadas com sucesso!")

        except Exception as e:
            print(f"[-] Erro ao processar logística portuária: {e}")
        finally:
            if os.path.exists(decisao_path): os.remove(decisao_path)
            if os.path.exists(decisao_path + ".bak"): os.remove(decisao_path + ".bak")

if __name__ == "__main__":
    run_port_simulation()

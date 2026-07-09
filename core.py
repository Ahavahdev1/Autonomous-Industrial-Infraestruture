import os
import sys
import json
import shutil
import subprocess
import logging
import math
import typing    # 1. Importa o typing
import builtins  # 2. Importa o builtins

# 3. Define o Any globalmente ANTES de importar o MEA
# Isso faz com que o 'Any' exista para todos os arquivos que forem carregados depois
builtins.Any = typing.Any 

import uuid
instance_key = f"MEA-AGIR-{uuid.uuid4()}"

# 4. SÓ AGORA você importa o MEA
import mea.config
from mea.security import SovereignGate, LogosConstitution, AgentRegistry
from mea.recon import ReconEngine
from mea.reliability import QuantumSREController
from mea.memory import JSONGibberlink, Mem0Gibberlink
from mea.cognition import CognitionEngine

def run_test_suite(test_command: str) -> tuple[bool, str]:
    """Executa os testes físicos do ambiente real com timeout estendido para repositórios Enterprise."""
    try:
        logging.info(f"Disparando testes físicos locais: {test_command}")
        print(f"[+] [HUNTER-LOOP] Compilando ambiente e rodando testes (Isso pode demorar em projetos grandes)...")
        
        # Aumentamos o timeout de 90s para 600s (10 minutos) para aguentar as bibliotecas do SWE-Bench
        result = subprocess.run(test_command, shell=True, capture_output=True, text=True, timeout=600)
        success = result.returncode == 0
        output = result.stdout + "\n" + result.stderr
        return success, output
    except subprocess.TimeoutExpired as e:
        msg = f"Timeout Físico: O teste demorou mais de 600 segundos para executar. {e}"
        logging.error(msg)
        return False, msg
    except Exception as e:
        return False, f"Falha catastrófica ao executar suíte de testes: {e}"


def execute_hunter_loop(target_filepath: str, test_cmd: str, master_key: str, instrucao_dev: str = None, image_paths: list = None):
    logging.info("Iniciando ciclo operacional Hunter-Loop.")
    print("======================================================================")
    print(" MEA v5.8.1 'AGIR' - SOVEREIGN ENGINE DE PRODUÇÃO")
    print("======================================================================\n")

    gate = SovereignGate(master_key)
    sre = QuantumSREController()
    cognition = CognitionEngine()

    # Validação da Vitalidade (Disjuntor Híbrido: Local + Oráculo Remoto)
    if not gate.check_vitality():
        logging.warning("SovereignGate bloqueado pelo Kill-Switch.")
        sys.exit(1)

    # Inicialização Dinâmica do Gibberlink baseada no GIBBERLINK_MODE do .env
    mode = os.getenv("GIBBERLINK_MODE", "json").lower()
    if mode == "mem0":
        try:
            gibberlink = Mem0Gibberlink()
            logging.info("Colmeia inicializada no modo semântico (Mem0).")
            print("[+] [SYSTEM] Matriz de Memória da Colmeia: modo semântico (Mem0) ativo.")
        except Exception as e:
            logging.error(f"Falha ao iniciar o Mem0: {e}. Revertendo para modo 'json'.")
            print("[-] [SYSTEM] Erro ao carregar Mem0. Revertendo para modo 'json'.")
            gibberlink = JSONGibberlink()
    elif mode == "redis":
        try:
            from mea.memory import RedisGibberlink
            gibberlink = RedisGibberlink()
            logging.info("Colmeia inicializada no modo centralizado (Redis).")
            print("[+] [SYSTEM] Matriz de Memória da Colmeia: modo centralizado (Redis) ativo.")
        except Exception as e:
            logging.error(f"Falha ao iniciar o Redis: {e}. Revertendo para modo 'json'.")
            print("[-] [SYSTEM] Erro ao carregar Redis. Revertendo para modo 'json'.")
            gibberlink = JSONGibberlink()
    else:
        gibberlink = JSONGibberlink()
        logging.info("Colmeia inicializada no modo estático (JSON).")
        print("[+] [SYSTEM] Matriz de Memória da Colmeia: modo estático (JSON) ativo.")

    # TAREFA 1.1: Isolamento de Soul Transfer por workspace/worker para evitar colisões em execuções paralelas
    # Usamos o nome do diretório do CWD como sufixo exclusivo para identificar cada agente de forma única
    workspace_name = os.path.basename(os.getcwd())
    soul_file = f"../soul_transfer_{workspace_name}.json"
    
    agent_state = {"generation": 1, "success_count": 0, "last_theta": math.pi/2}
    
    if os.path.exists(soul_file):
        try:
            with open(soul_file, "r") as f:
                payload = json.load(f)
            if gate.verify_soul(payload["state"], payload["signature"]):
                agent_state = payload["state"]
                agent_state["generation"] += 1
                sre.theta = agent_state["last_theta"]
                logging.info(f"Soul Transfer validada com sucesso. Reencarnação Geração {agent_state['generation']}")
                print(f"[+] [SOUL-TRANSFER] Reencarnação bem-sucedida! Geração {agent_state['generation']} acordada.")
            else:
                logging.warning("ALERTA: Tentativa de Soul Transfer com assinatura inválida/corrompida.")
                print("[-] [SOUL-TRANSFER] ALERTA: Assinatura da alma corrompida. Vetando estado antigo.")
        except Exception as e:
            logging.error(f"Erro ao carregar alma: {e}")

    passed = False  
    is_benchmark = os.getenv("MEA_BENCHMARK", "False").lower() in ("true", "1")

    # Registro de Nascimento (Boot) conforme o Fluxograma da Seção 6
    # Nota: 'mode' é a variável definida no bloco anterior de inicialização do Gibberlink
    AgentRegistry.register_boot(
        instance_key=instance_key, 
        generation=agent_state.get("generation", 1), 
        mode_type=mode, 
        theta=sre.theta
    )
    logging.info(f"Instância registrada no Ledger: {instance_key} [Boot]")

    primeira_verificacao = True
    ultimo_erro = ""

    # Configuração de limites: 4 tentativas no benchmark, 999 na conversação ativa
    max_attempts = 4 if is_benchmark else 999
    attempt = 0

    while attempt < max_attempts:
        attempt += 1
        
        if is_benchmark:
            logging.info(f"Iniciando ciclo {attempt} de {max_attempts} no benchmark.")
            print(f"\n [MEA-ITERATION] Iniciando ciclo {attempt}/{max_attempts} no benchmark...")
        else:
            logging.info(f"Iniciando ciclo {attempt} no modo conversação.")
            print(f"\n [MEA-ITERATION] Iniciando ciclo {attempt} no modo ativo...")

        # Execução da suíte de testes (Aqui a variável 'passed' recebe seu valor real)
        passed, test_output = run_test_suite(test_cmd)
        ultimo_erro = test_output if not passed else ""

        if passed:
            logging.info("Testes físicos passaram. Sistema estável.")
            print("[+] [HUNTER-LOOP] Excelente. Todos os testes estão passando. O sistema está estável.")
            if is_benchmark:
                logging.info("Benchmark resolvido com sucesso.")
                break
        else:
            logging.warning("Falha física nos testes detectada.")
            print("[-] [HUNTER-LOOP] Falhas nos testes detectadas.")
            
            if ultimo_erro:
                linhas_erro = ultimo_erro.strip().splitlines()
                print("\n  --- RASTREAMENTO DO ERRO ATUAL NOS TESTES ---")
                for linha in linhas_erro[-15:]:
                    print(f"   | {linha}")
                print("   ------------------------------------------------\n")


        if is_benchmark:
            user_instruction = instrucao_dev if instrucao_dev else "Corrija os erros encontrados."
        else:
            print("\n-------------------------------------------------------------")
            print("   CONVERSAÇÃO ATIVA - MEA v5.8.1")
            print("   Insira sua instrução de ajuste (ex: 'adicione tratamento de erros')")
            print("   Ou aperte [ENTER] em branco (ou 'sair') para registrar com sucesso.")
            print("-------------------------------------------------------------")
            user_instruction = input("Sua instrução >> ").strip()

            if user_instruction.lower() in ("sair", "exit", "quit") or (not user_instruction and passed):
                logging.info("Loop de conversação encerrado pelo usuário.")
                break
            
            if not user_instruction and not passed:
                user_instruction = "Corrija os erros indicados nos testes."

        logging.info(f"Iniciando procedimento de cirurgia de código em '{target_filepath}'")
        backup_path = target_filepath + ".bak"
        shutil.copy2(target_filepath, backup_path)
        
        vaccines = gibberlink.fetch_vaccines(ultimo_erro)
        proposed_code = cognition.generate_patch(
        filepath=target_filepath, 
        error_log=ultimo_erro, 
        vaccines=vaccines, 
        instruction=user_instruction,
        image_paths=image_paths # <<< ESTE É O PARÂMETRO MULTIMODAL INJETADO
    )

        logging.info("Enviando código gerado para a verificação do Logos Constitution.")
        if not LogosConstitution.verify_action(target_filepath, proposed_code):
            logging.warning("Código gerado rejeitado pelo Logos Constitution.")
            if os.path.exists(backup_path): 
                os.remove(backup_path)
            print("[-] [LOGOS] Código quebrou regras sintáticas. Pulando para próxima iteração...")
            continue

        with open(target_filepath, "w", encoding="utf-8") as f:
            f.write(proposed_code)
        logging.info(f"Patch gravado fisicamente no arquivo '{target_filepath}'")

        passed_after, new_test_output = run_test_suite(test_cmd)
        ultimo_erro = new_test_output if not passed_after else ""

        if passed_after:
            logging.info("Patch aplicado com sucesso. Testes estabilizados.")
            sre.rotate(success=True)
            agent_state["success_count"] += 1
            passed = True
            if os.path.exists(backup_path):
                os.remove(backup_path)
            print("[+] [HUNTER-LOOP] SUCESSO! O patch corrigiu o bug e todos os testes passaram.")
            break
        else:
            logging.warning("O patch falhou ao tentar estabilizar os testes.")
            sre.rotate(success=False, severity=0.8)
            
            decision = sre.collapse()
            if decision == "ROLLBACK":
                logging.info(f"QuantumSRE acionou ROLLBACK para '{target_filepath}'")
                print("[-] [QUANTUM-SRE] SRE colapsou em ROLLBACK. Restaurando backup funcional anterior...")
                shutil.copy2(backup_path, target_filepath)
            else:
                logging.info(f"QuantumSRE acionou PROCEED experimental para '{target_filepath}'")
                print("[~] [QUANTUM-SRE] SRE colapsou em PROCEED. Mantendo patch experimental para próxima iteração...")
                gibberlink.publish_insight(
                    error_pattern=new_test_output[:100], 
                    fix_pattern="Evitar esta reescrita sintática nesta versão de interpretador."
                )
            if os.path.exists(backup_path):
                os.remove(backup_path)

        if is_benchmark and attempt >= max_attempts:
            logging.warning("Atingido o limite máximo de tentativas de reparo no benchmark.")
            print(f"[-] [HUNTER-LOOP] Atingido o limite de {max_attempts} tentativas de reparo sem sucesso.")
            break

    # Sorteio e registro final de encerramento controlado
    agent_state["last_theta"] = sre.theta
    soul_signature = gate.sign_soul(agent_state)
    
    with open(soul_file, "w") as f:
        json.dump({"state": agent_state, "signature": soul_signature}, f, indent=4)
    
    # Registro de morte controlada no Ledger
    AgentRegistry.register_shutdown(instance_key, "SUCCESS" if passed else "FAILED", sre.theta)

    logging.info("Estado da alma criptografado e salvo com sucesso.")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(1)
        
    target = sys.argv[1]
    cmd = sys.argv[2]
    instrucao_dev = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Se houver uma lista de caminhos de imagem passados como o quarto argumento em JSON:
    # ex: python core.py main.py "pytest" "instrucao" '["screenshot.png"]'
    image_paths = None
    if len(sys.argv) > 4:
        try:
            image_paths = json.loads(sys.argv[4])
        except:
            pass
            
    master_key = os.getenv("MEA_SOVEREIGN_KEY", "SUA_CHAVE_MESTRA_DE_SOBERANIA")
    execute_hunter_loop(
        target_filepath=target,
        test_cmd=cmd,
        master_key=master_key,
        instrucao_dev=instrucao_dev,
        image_paths=image_paths # <<< INJETADO NA INICIALIZAÇÃO DO TERMINAL
    )
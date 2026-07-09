# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.4 "AGIR" - NÚCLEO DE DECISÃO SOBERANA E EXECUÇÃO FÍSICA
#  Copyright (c) 2026 Bruno Loureiro Desidera. All rights reserved.
# ==============================================================================
import os
import sys
import json
import asyncio
import requests
import re
import logging
import subprocess
from fastapi import Form, WebSocket
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

# Imports de segurança e reconhecimento do seu pacote local
from mea.security import SovereignGate, LogosConstitution
from mea.recon import ReconEngine
from mea.guardian import GuardianEngine
from mea.evolution import EvolutionaryPatcher


class MEALogRedirector:
    """Intercepta o sys.stdout em tempo de execução para alimentar o WebSocket."""
    def __init__(self, log_filepath="system_audit.log"):
        self.log_filepath = log_filepath
        self.terminal = sys.stdout

    def write(self, message):
        self.terminal.write(message)
        mensagem_limpa = message.strip()
        if mensagem_limpa:
            try:
                with open(self.log_filepath, "a", encoding="utf-8", errors="ignore") as f:
                    f.write(f"[COLMEIA] {mensagem_limpa}\n")
            except Exception:
                pass

    def flush(self):
        if self.terminal:
            self.terminal.flush()


class MEA:
    """A Classe Soberana: Kernel de decisão de nível SRE."""
    def __init__(self, client, app=None, model="gpt-4o-mini"):
        self.app = app
        self.client = client
        self.model = model
        self.master_key = os.getenv("MEA_SOVEREIGN_KEY", "SUA_CHAVE_MESTRA_DE_SOBERANIA")
        self.cache_bounties = []
        self.guardian = GuardianEngine()
        self.logger = logging.getLogger("MEA.Kernel")
        
        if self.app:
            self.registrar_rotas()

    def registrar_rotas(self):
        """Interface Web de Gestão e WebSockets."""
        directory_name = "front" if os.path.exists("front") else "frontend"
        if not os.path.exists(directory_name):
            os.makedirs(directory_name, exist_ok=True)
            with open(os.path.join(directory_name, "index.html"), "w") as f:
                f.write("<!-- MEA Terminal Active -->")

        self.app.mount("/static", StaticFiles(directory=directory_name), name="static")

        @self.app.get("/")
        async def read_index():
            return FileResponse(f"{directory_name}/index.html")

        @self.app.get("/api/status")
        async def status():
            return {
                "queue_pending": 0, 
                "current_task": "idle", 
                "alma_restaurada": True,
                "cache_size": len(self.cache_bounties)
            }

        @self.app.websocket("/api/ws/logs")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            log_file = "system_audit.log"
            if not os.path.exists(log_file):
                with open(log_file, "w", encoding="utf-8") as f:
                    f.write("--- INICIANDO BARRAMENTO DE AUDITORIA MEA ---\n")

            try:
                with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
                    f.seek(0, os.SEEK_END)
                    while True:
                        linha = f.readline()
                        if not linha:
                            await asyncio.sleep(0.4)
                            continue
                        
                        linha_limpa = linha.strip()
                        if linha_limpa:
                            status = "info"
                            step = "sistema"
                            
                            if any(x in linha_limpa for x in ["SUCESSO", "estável", "validada", "RESOLVIDO"]):
                                status = "success"; step = "sucesso"
                            elif any(x in linha_limpa for x in ["Falha", "ERROR", "bloqueado", "Erro"]):
                                status = "failed"; step = "falha"
                            elif "COLMEIA" in linha_limpa: step = "colmeia"
                            elif "RECON" in linha_limpa: step = "recon"
                                
                            await websocket.send_json({"step": step, "message": linha_limpa, "status": status})
            except Exception:
                pass

        @self.app.post("/api/interagir")
        async def interagir(prompt: str = Form(...)):
            from mea.intention import IntentionBridge
            bridge = IntentionBridge()
            decisao = await bridge.traduzir_comando(prompt)
            resposta = await self.processar_comando(prompt, decisao)
            return {"status": "chat", "response": resposta}

    async def processar_comando(self, prompt: str, decisao: dict) -> str:
        """
        Kernel de Decisão: Unifica o Terminal e a Web.
        """
        gate = SovereignGate(self.master_key)
        if not gate.check_vitality():
            return "SISTEMA BLOQUEADO: Vitalidade remota negativa."

        funcao = decisao.get("funcao")
        args = decisao.get("args", [])

        try:
            if funcao == 'atacar_alvo':
                return await self._handle_ataque(args, prompt)
            
            elif funcao == 'buscar_bounty':
                return await self._handle_recon(args)
            
            elif funcao == 'sistema_os':
                return await self._handle_os_action(args)
            
            else:
                return await self._gerar_conversa_ia(prompt)
        except Exception as e:
            self.logger.error(f"Falha na decisão: {e}")
            return f"Erro de kernel: {str(e)}"

    async def _handle_ataque(self, args, prompt) -> str:
        """Gerencia o Hunter-Loop com suporte a alvos diretos, repositórios e auto-cura Mt 5:8."""
        target_input = str(args[0]).strip('"').strip("'")
        
        repo_url = target_input
        repo_dir = "./alvo_temp"
        
        # 1. Resolução de Índice para Bounties
        if target_input.isdigit():
            idx = int(target_input)
            if self.cache_bounties and idx < len(self.cache_bounties):
                issue_obj = self.cache_bounties[idx]
                repo_url = issue_obj.get('html_url', '').split('/issues/')[0]
                repo_dir = f"./alvo_{idx}"
            else:
                return f"Erro: Índice {idx} não encontrado no cache."

        # 2. Clonagem ou uso direto
        if "github.com" in repo_url:
            if not os.path.exists(repo_dir):
                token = os.getenv("GITHUB_TOKEN")
                auth_url = f"https://{token}@github.com/{repo_url.split('github.com/')[-1]}.git"
                subprocess.run(["git", "clone", "--depth", "1", auth_url, repo_dir], capture_output=True)
            repo_path = repo_dir
        else:
            repo_path = target_input

        # 3. INTERCEPTAÇÃO MT 5:8 - CONSENSO SOBERANO & AUTO-CURA DE CAMINHO
        from mea.Mt5_8 import ConsensoSoberano
        consenso = ConsensoSoberano()
        
        # O Consenso analisa a intencionalidade (Logica/Memoria) e cura a Execução fisicamente
        consenso_atingido, caminho_curado = consenso.verificar_e_curar(
            logica=True, 
            memoria=True, 
            target_path=repo_path
        )
        
        if not consenso_atingido:
            return f"Erro: Alvo '{repo_path}' falhou no Consenso Soberano Mt 5:8 (Sem união com Execução)."

        # O alvo agora passa a ser o caminho curado e validado autonomamente
        repo_path = caminho_curado
        abs_target = os.path.abspath(repo_path)

        # 4. Test_cmd dinâmico baseado no alvo curado
        if abs_target.endswith(".ex"):
            test_cmd = args[1] if len(args) > 1 else f"elixirc {abs_target}"
        else:
            test_cmd = args[1] if len(args) > 1 else f'"{sys.executable}" -m py_compile "{abs_target}"'

        # 5. Bypass de ReconEngine se o alvo for direto e validado no consenso
        if os.path.exists(abs_target):
            alvos = [abs_target]
        else:
            alvos = [item['path'] for item in ReconEngine.map_repository(abs_target)]

        if alvos:
            # Garante que o Hunter-Loop rode no contexto de thread correto
            asyncio.create_task(asyncio.to_thread(self._run_swarm, alvos[0], test_cmd, prompt))
            return f"🚀 Hunter-Loop acionado no alvo curado: {alvos[0]}."
        
        return f"Erro: Alvo '{abs_target}' não pôde ser mapeado após a verificação de consenso."

    def _run_swarm(self, target, cmd, inst):
        from core import execute_hunter_loop
        execute_hunter_loop(target, cmd, self.master_key, inst)

    async def _handle_os_action(self, args) -> str:
        """Músculos de execução física com auditoria rigorosa."""
        try:
            acao = str(args[0]).lower().replace("funcao_", "").strip()
            target = str(args[1]).replace("arquivo ", "").strip() if len(args) > 1 else ""
            payload = args[2] if len(args) > 2 else ""

            # 1. Leitura de arquivos
            if any(k in acao for k in ["read", "ler", "leitura"]):
                if not os.path.exists(target): return f"Erro: '{target}' não existe."
                with open(target, "r", encoding="utf-8", errors="ignore") as f:
                    return f"📄 CONTEÚDO DE '{target}':\n\n{f.read(3000)}"

            # 2. Escrita de arquivos (Guardian blindado)
            if any(k in acao for k in ["write", "criar", "crie", "create", "gravar"]):
                if not target: return "Erro: Alvo não especificado."
                self.guardian.enforce(target, payload)
                if not LogosConstitution.verify_action(target, payload):
                    return "Ação bloqueada pela Constituição Logos."
                
                if os.path.dirname(target): os.makedirs(os.path.dirname(target), exist_ok=True)
                with open(target, "w", encoding="utf-8") as f: f.write(payload)
                return f"✨ SUCESSO FÍSICO: Arquivo '{target}' criado."

            # 3. Execução de binários/scripts
            if any(k in acao for k in ["executar", "rodar", "run", "execute"]):
                if not target or not os.path.exists(target): return f"Erro: '{target}' não encontrado."
                proc = await asyncio.to_thread(subprocess.run, [sys.executable, target], capture_output=True, text=True)
                return f"✅ RESULTADO:\n{proc.stdout or proc.stderr}"

            return f"Comando físico '{acao}' não mapeado."
        except Exception as e:
            return f"Falha física: {str(e)}"

    async def _handle_recon(self, args) -> str:
        """Escaneamento de mercado (Bounties)."""
        min_v = float(args[0]) if len(args) > 0 else 200.0
        url = "https://api.github.com/search/issues?q=is:issue+is:open+label:bounty+language:python&sort=updated"
        headers = {"Authorization": f"token {os.getenv('GITHUB_TOKEN')}"}
        try:
            res = requests.get(url, headers=headers, timeout=15).json()
            items = res.get("items", [])[:5]
            if not items: return "GitHub retornou lista vazia."
            self.cache_bounties = items
            resposta = "🎯 **Bounties Python:**\n\n"
            for idx, item in enumerate(items):
                resposta += f"[{idx}] {item['title']}\n    🔗 {item['html_url']}\n\n"
            return resposta + "Qual missão vamos atacar?"
        except Exception as e: return f"Erro no Recon: {e}"

    async def _gerar_conversa_ia(self, prompt: str) -> str:
        """Núcleo Cognitivo com System Prompt Soberano."""
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": "Você é o MEA v10.6.4, operador soberano de Bruno Loureiro. Aja fisicamente no sistema quando solicitado."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            return response.choices[0].message.content
        except Exception as e: return f"Falha cognitiva: {e}"
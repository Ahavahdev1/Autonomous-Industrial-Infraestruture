# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA — GitOpsManager v10.6.4 (SRE Headless CD Engine)
#  Gerenciamento de Deploy Headless com Validação de Consenso e Auto-Remediação.
#  Copyright (c) 2026 Bruno Loureiro Desidera. All rights reserved.
# ==============================================================================
import os
import sys
import json
import urllib.request
import urllib.parse
import urllib.error
import subprocess
import time
import logging

class GitOpsManager:
    """
    Gerencia o ciclo de entrega contínua (CD) de forma 100% HEADLESS.
    Injeta credenciais via URL e protege o deploy usando o Consenso Soberano.
    """
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.owner = os.getenv("GITHUB_OWNER")
        self.repo = os.getenv("GITHUB_REPO")
        self.logger = logging.getLogger("mea.GitOps")
        
    def verificar_credenciais(self) -> bool:
        return bool(self.token and self.owner and self.repo)

    def _executar(self, cmd: list) -> tuple[int, str, str]:
        try:
            env = os.environ.copy()
            env["PYTHONIOENCODING"] = "utf-8"
            process = subprocess.run(cmd, capture_output=True, encoding="utf-8", errors="ignore", env=env)
            return process.returncode, process.stdout.strip(), process.stderr.strip()
        except Exception as e:
            return -1, "", str(e)

    def criar_branch_e_push(self, arquivos: list, prompt: str) -> tuple[bool, str, str]:
        """
        Garante a integridade do deploy rodando o Consenso Mt 5:8 antes do push.
        Adiciona apenas arquivos específicos para evitar vazamento do .env ou mea/.
        """
        if not self.verificar_credenciais():
            return False, "", "Credenciais ausentes no .env"

        # ======================================================================
        # 1. CONSENSO SOBERANO (Mt 5:8) - O PORTÃO DE PUREZA ANTES DO DEPLOY
        # ======================================================================
        from mea.Mt5_8 import ConsensoSoberano
        consenso = ConsensoSoberano()

        for arq in arquivos:
            # O Consenso verifica se o arquivo é real e se passou pela Constituição Logos
            consenso_atingido, caminho_real = consenso.verificar_e_curar(
                logica=True, 
                memoria=True, 
                target_path=arq
            )
            
            if not consenso_atingido:
                self.log_evento_interno(f"❌ VETO DE DEPLOY: Arquivo '{arq}' falhou no Consenso Soberano.")
                self.logger.critical(f"GITOPS | Deploy abortado devido a impureza em '{arq}'.")
                return False, "", f"Deploy vetado por violação de integridade em '{arq}' (Mt 5:8)"

        # ======================================================================
        # 2. PREPARAÇÃO LOCAL E COMMIT ATÔMICO
        # ======================================================================
        branch_name = f"evolucao-{int(time.time())}"
        self.log_evento_interno(f"Consenso Atingido. Criando branch de entrega: {branch_name}")
        
        self._executar(["git", "checkout", "-b", branch_name])
        
        # Adiciona APENAS os arquivos autorizados do deploy (evita vazar o .env ou a pasta mea/)
        for arq in arquivos:
            if os.path.exists(arq):
                self._executar(["git", "add", arq])

        commit_msg = f"fix(autonomo): {prompt[:50]}"
        ret, out, err = self._executar(["git", "commit", "-m", commit_msg])
        
        if ret != 0 and "nothing to commit" not in out:
            self._executar(["git", "checkout", "main"])
            return False, "", f"Erro no commit local: {err}"

        # ======================================================================
        # 3. PUSH HEADLESS SOBERANO (Token embutido)
        # ======================================================================
        authenticated_url = f"https://{self.token}@github.com/{self.owner}/{self.repo}.git"
        self.log_evento_interno(f"Iniciando Push Headless Silencioso...")
        
        ret_p, out_p, err_p = self._executar(["git", "push", authenticated_url, branch_name])

        if ret_p != 0:
            self._executar(["git", "checkout", "main"]) # Recuo preventivo por segurança
            return False, "", f"Falha no Push Remoto: {err_p}"

        self._executar(["git", "checkout", "main"])
        self.logger.info(f"GITOPS | Push concluído com sucesso para branch {branch_name}.")
        return True, branch_name, ""

    def criar_pull_request(self, branch_name: str, prompt: str) -> tuple[bool, str]:
        url = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls"
        payload = {
            "title": f"🧬 MEA v10.6.4: {prompt[:60]}",
            "body": (
                f"## Evolução Autônoma de Nível 5\n\n"
                f"**Solicitação:** {prompt}\n\n"
                f"*Este PR foi validado, testado e enviado pelo ecossistema de Consenso Soberano MEA.*"
            ),
            "head": branch_name,
            "base": "main"
        }

        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Authorization", f"Bearer {self.token}")
        req.add_header("Accept", "application/vnd.github+json")
        req.add_header("User-Agent", "MEA-Headless-Agent")

        try:
            with urllib.request.urlopen(req, timeout=15) as response:
                res = json.loads(response.read().decode("utf-8"))
                return True, res.get("html_url")
        except Exception as e:
            return False, str(e)

    def buscar_comentarios_pr(self, pr_number: int) -> list:
        """
        Consulta os comentários de revisão feitos por humanos no PR.
        Suporta tanto comentários de linha (review) quanto discussões gerais (issues).
        """
        if not self.verificar_credenciais():
            return []
            
        url_review = f"https://api.github.com/repos/{self.owner}/{self.repo}/pulls/{pr_number}/comments"
        url_issue = f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{pr_number}/comments"
        
        comentarios_filtrados = []
        for url in [url_review, url_issue]:
            req = urllib.request.Request(url, method="GET")
            req.add_header("Authorization", f"Bearer {self.token}")
            req.add_header("Accept", "application/vnd.github+json")
            req.add_header("User-Agent", "MEA-Headless-Agent")
            try:
                with urllib.request.urlopen(req, timeout=10) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    for comment in data:
                        body = comment.get("body", "")
                        user = comment.get("user", {}).get("login", "unknown")
                        if body:
                            comentarios_filtrados.append(f"[@{user}]: {body}")
            except Exception as e:
                self.logger.warning(f"GITOPS | Falha ao buscar comentários de {url}: {e}")
                
        return comentarios_filtrados

    def log_evento_interno(self, msg):
        print(f"[MEA GIT] {msg}")
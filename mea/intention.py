# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA — IntentionBridge (v10.6.4 "AGIR")
#  Protocolo de Triagem e Classificação Semântica de Intenções do Operador
#  Copyright (c) 2026 Bruno Loureiro Desidera. All rights reserved.
# ==============================================================================
import os
import json
import logging
from openai import AsyncOpenAI

class IntentionBridge:
    """O Córtex Intencional do MEA. Decide e roteia entre conversa e ação física."""
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        self.logger = logging.getLogger("mea.Intention")

    async def traduzir_comando(self, usuario_input: str) -> dict:
        """
        Analisa a entrada do usuário e mapeia para a função física do Kernel correspondente,
        com tratamento estrito para evitar vazamento de parâmetros e comandos de testes fictícios.
        """
        if not self.api_key:
            self.logger.critical("INTENTION | OPENAI_API_KEY ausente no ambiente.")
            return {"funcao": "conversa", "args": []}

        # Prompt de Triagem Robusto com 4 Regras de Consenso
        prompt = f"""
        Você é o Protocolo de Triagem e Córtex Intencional do MEA v10.6.4.
        Sua única função é traduzir a intenção semântica do usuário em uma chamada de função estruturada do nosso Kernel de Controle.

        [INPUT DO USUÁRIO]: "{usuario_input}"

        REGRAS DE CLASSIFICAÇÃO SOBERANAS:
        1. Se for apenas conversa, dúvida, pitch, saudação, feedback ou comentário geral:
           Retorne: {{"funcao": "conversa", "args": []}}

        2. Se for uma busca por issues de recompensa (bounties) no GitHub:
           Retorne: {{"funcao": "buscar_bounty", "args": [min_usd]}} (se não houver valor mínimo, envie 200.0)

        3. Se for um comando de engenharia/ataque a bugs em um repositório ou arquivo existente (Hunter-Loop):
           Retorne: {{"funcao": "atacar_alvo", "args": ["caminho_ou_indice", "comando_de_teste"]}}
           * IMPORTANTE: O "comando_de_teste" (args[1]) DEVE ser um comando de terminal real válido (como "elixirc" ou "pytest") que o usuário especificou.
           * Se o usuário NÃO especificou um comando de teste, retorne o segundo argumento estritamente como null ou remova-o.
           * NUNCA coloque palavras do comando como "atacar", "atacar_alvo", "missão" ou "reparo" no campo de comando de teste.

        4. Se for uma AÇÃO FÍSICA no sistema operacional (como ler um arquivo, escrever/criar um arquivo, ou executar um script local):
           Retorne: {{"funcao": "sistema_os", "args": ["acao", "target", "texto_ou_payload", "sub_acao"]}}
           * "acao" deve ser: "read_file" (para ler/visualizar), "write_file" (para criar/gravar) ou "executar" (para rodar scripts/arquivos)
           * "target" deve ser o caminho relativo ou absoluto do arquivo ou pasta alvo.
           * "texto_ou_payload" deve conter o conteúdo bruto do arquivo que o usuário quer escrever (se aplicável).
           * "sub_acao" deve ser null, a menos que o usuário queira registrar uma ferramenta (ex: "register_local_tool").

        Sua resposta deve ser estritamente um JSON válido de acordo com o esquema acima, sem explicações ou markdown.
        """

        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.0 # Zero alucinação para máxima exatidão
            )
            
            result_text = response.choices[0].message.content.strip()
            decisao = json.loads(result_text)
            
            funcao = decisao.get("funcao", "conversa")
            args = decisao.get("args", [])
            
            # --- BLINDAGEM CONTRA O BUG DO 'ATACAR' ---
            # Se a IA alucinar e colocar "atacar" como comando de teste, nós higienizamos ativamente aqui
            if funcao == "atacar_alvo" and len(args) > 1:
                test_cmd = str(args[1]).strip().lower()
                if test_cmd in ["atacar", "atacar_alvo", "attack", "test", "teste", "pytest_ignorar", "null", "none"]:
                    decisao["args"] = [args[0]] # Remove o argumento fictício para forçar o chat.py a usar o elixirc/py_compile padrão

            return decisao
            
        except Exception as e:
            self.logger.error(f"INTENTION | Falha crítica na triagem: {e}")
            return {"funcao": "conversa", "args": []}
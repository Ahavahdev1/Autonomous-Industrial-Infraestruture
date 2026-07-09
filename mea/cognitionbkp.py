import os
import sys
import json
import logging
import re
from typing import Any

class CognitionEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        # Lê o modelo de forma dinâmica do .env (se omitido, o padrão será gpt-4o)
        self.model = os.getenv("COGNITION_MODEL", "gpt-4o")

    def _apply_search_replace_blocks(self, original_code: str, patch_text: str) -> str:
        """
        Analisa os blocos <<<<<<< SEARCH / ======= / >>>>>>> REPLACE gerados pelo LLM
        e aplica as edições cirurgicamente ao código original.
        """
        # MODIFICADO: Regex flexível que aceita de 5 a 8 sinais de comparação,
        # tolerando desvios de geração do LLM (como o surgimento de apenas 6 caracteres '>')
        pattern = re.compile(
            r"<" + r"{5,8} SEARCH[\r\n]*(.*?)[\r\n]*"
            r"=" + r"{5,8}[\r\n]*(.*?)[\r\n]*"
            r">" + r"{5,8} REPLACE",
            re.DOTALL
        )
        
        blocks = pattern.findall(patch_text)
        if not blocks:
            # Fallback de segurança: Se por algum motivo o modelo ignorar a regra e retornar
            # o código completo de qualquer forma, tentamos usar como fallback.
            cleaned = patch_text.strip()
            if "def " in cleaned or "import " in cleaned or "class " in cleaned:
                logging.warning("COGNITION | Modelo não usou blocos SEARCH/REPLACE, aplicando fallback de arquivo completo.")
                return patch_text
            raise ValueError(
                "O modelo não retornou nenhum bloco <<<<<<< SEARCH ... ======= ... >>>>>>> REPLACE válido."
            )

        modified_code = original_code
        for idx, (search_block, replace_block) in enumerate(blocks, start=1):
            # Normalização simples de quebra de linha para evitar falhas de correspondência literal (\r\n vs \n)
            search_norm = search_block.replace("\r\n", "\n").strip()
            
            # Tentativa 1: Correspondência literal exata com quebras originais
            if search_block in modified_code:
                modified_code = modified_code.replace(search_block, replace_block, 1)
                logging.info(f"COGNITION | Bloco #{idx} de SEARCH/REPLACE aplicado com sucesso (Casamento exato).")
            # Tentativa 2: Correspondência literal flexível (removendo espaços das pontas do bloco de busca)
            elif search_block.strip() in modified_code:
                modified_code = modified_code.replace(search_block.strip(), replace_block, 1)
                logging.info(f"COGNITION | Bloco #{idx} de SEARCH/REPLACE aplicado com sucesso (Casamento flexível).")
            else:
                # Tentativa 3: Correspondência normalizada em sistemas que misturam quebras de linha
                modified_norm = modified_code.replace("\r\n", "\n")
                if search_norm in modified_norm:
                    modified_norm = modified_norm.replace(search_norm, replace_block.replace("\r\n", "\n"), 1)
                    modified_code = modified_norm
                    logging.info(f"COGNITION | Bloco #{idx} de SEARCH/REPLACE aplicado com sucesso (Casamento normalizado).")
                else:
                    logging.error(f"COGNITION | Falha ao casar Bloco #{idx}:\n{search_block}")
                    raise ValueError(
                        f"Não foi possível encontrar o trecho de busca original no arquivo para o Bloco #{idx}."
                    )
                    
        return modified_code

    def generate_patch(self, filepath: str, error_log: str, vaccines: Any, instruction: str = None) -> str:
        if not self.api_key:
            logging.critical("COGNITION | Chamada cognitiva abortada: API key ausente.")
            sys.exit(1)

        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)

        with open(filepath, "r", encoding="utf-8") as f:
            current_code = f.read()

        prompt = f"""
        Você é o córtex cognitivo do MEA v5.8.1 AGIR.
        Sua tarefa é modificar cirurgicamente o arquivo '{os.path.basename(filepath)}' seguindo a instrução do desenvolvedor ou corrigindo o erro indicado nos testes.

        INSTRUÇÃO DO DESENVOLVEDOR (SE HOUVER):
        {instruction if instruction else "Nenhuma instrução específica fornecida."}

        CÓDIGO ATUAL DO ARQUIVO:
        ```python
        {current_code}
        ```

        LOG DE ERRO DO COMPILADOR/TESTES:
        ```
        {error_log}
        ```

        CONHECIMENTO ADAPTATIVO COMPARTILHADO (GIBBERLINK VACCINES):
        {json.dumps(vaccines, indent=2)}

        REGRAS CRÍTICAS DE RESPOSTA (FORMATO SEARCH/REPLACE):
        Sua resposta deve conter APENAS as edições necessárias ao arquivo original usando um ou mais blocos SEARCH/REPLACE.
        Não reescreva o arquivo inteiro se não for estritamente necessário.
        Não adicione explicações, introduções ou notas adicionais.
        
        Você deve responder usando estritamente o formato abaixo para cada alteração:

        <<<<<<< SEARCH
        [insira aqui o trecho exato de código do arquivo atual que precisa ser modificado]
        =======
        [insira aqui o novo código modificado que substituirá o trecho acima]
        >>>>>>> REPLACE
        """

        try:
            # TELEMETRIA: Log alterado para exibir qual modelo está sendo acionado em tempo de execução
            logging.info(f"COGNITION | Disparando chamada LLM ({self.model}) para reparar '{os.path.basename(filepath)}'")
            response = client.chat.completions.create(
                model=self.model, # MODIFICADO: Usa o modelo dinâmico configurado no seu .env
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0  # Temperatura 0.0 garante o determinismo na geração de código
            )
            raw_output = response.choices[0].message.content.strip()

            if hasattr(response, "usage") and response.usage:
                logging.info(f"COGNITION | Tokens consumidos: Prompt={response.usage.prompt_tokens}, Comp={response.usage.completion_tokens}")
                print(f"[METRICS-DATA] prompt_tokens={response.usage.prompt_tokens} completion_tokens={response.usage.completion_tokens}")

            # Limpa delimitações markdown gerais se o modelo colocar o bloco inteiro em blocos de código
            if raw_output.startswith("```"):
                lines = raw_output.splitlines()
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].startswith("```"):
                    lines = lines[:-1]
                raw_output = "\n".join(lines)

            # Aplica os blocos SEARCH/REPLACE no código atual e reconstrói o arquivo completo
            logging.info("COGNITION | Aplicando blocos SEARCH/REPLACE recebidos no arquivo local...")
            modified_full_code = self._apply_search_replace_blocks(current_code, raw_output)
            
            return modified_full_code
            
        except Exception as e:
            logging.error(f"COGNITION | Erro no processamento cognitivo ou na aplicação do patch: {e}")
            # Se a resposta do LLM chegou a ser gerada antes da quebra do parser, exibe no terminal
            if 'raw_output' in locals():
                print("\n🔍 [MEA-DEBUG] RESPOSTA BRUTA DO MODELO QUE FALHOU NO PARSER:")
                print("======================================================================")
                print(raw_output)
                print("======================================================================\n")
            raise e #
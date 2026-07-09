import os
import sys
import json
import logging
import re
import time
import base64
from typing import Any
from openai import OpenAI
from mea.guardian import GuardianEngine, SecurityViolationError

class CognitionEngine:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("COGNITION_MODEL", "gpt-4o-mini") 
        self.base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.guardian = GuardianEngine()
        logging.info(f"COGNITION | Motor de Cognição Ativo. Modelo: '{self.model}'")

    def get_history_of_failures(self, filepath: str) -> str:
        log_path = "system_audit.log"
        if not os.path.exists(log_path):
            return ""
        try:
            filename = os.path.basename(filepath)
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            recent_errors = []
            for line in lines[-100:]:
                if filename in line and any(word in line for word in ["Erro", "Falha", "ValueError", "Violation"]):
                    recent_errors.append(line.strip())
            if recent_errors:
                history = "\n".join(recent_errors[-3:])
                return f"\n⚠️ HISTÓRICO DE TENTATIVAS ANTERIORES (Analise e NÃO repita os mesmos erros):\n{history}\n"
            return ""
        except:
            return ""

    def _normalize_line(self, line: str) -> str:
        line = line.split('#')[0]
        line = line.split('//')[0]
        line = re.sub(r'\s+', '', line)
        return line.replace("'", '"')

    def _encode_image_to_base64(self, image_path: str) -> str:
        if not os.path.exists(image_path):
            return ""
        ext = os.path.splitext(image_path)[1].lower()
        mime_type = "image/png" if ext == ".png" else "image/jpeg"
        try:
            with open(image_path, "rb") as image_file:
                b64_data = base64.b64encode(image_file.read()).decode("utf-8")
            return f"data:{mime_type};base64,{b64_data}"
        except Exception as e:
            return ""

    def _apply_search_replace_blocks(self, original_code: str, patch_text: str) -> str:
        pattern = re.compile(
            r"<{3,15}\s*SEARCH[\r\n]*(.*?)[\r\n]*"
            r"={3,15}\s*(?:REPLACE)?\s*[\r\n]*(.*?)[\r\n]*"
            r">{3,15}\s*REPLACE",
            re.DOTALL
        )
        blocks = pattern.findall(patch_text)
        if not blocks:
            cleaned = patch_text.strip()
            if "def " in cleaned or "import " in cleaned or "class " in cleaned or "defmodule " in cleaned:
                logging.warning("COGNITION | Fallback de código completo acionado.")
                markdown_block = re.search(r"```(?:\w*)?[\r\n]*(.*?)[\r\n]*```", cleaned, re.DOTALL)
                if markdown_block:
                    return markdown_block.group(1)
                return cleaned
            with open("failed_patch_debug.txt", "w", encoding="utf-8") as f:
                f.write(patch_text)
            raise ValueError("O modelo não retornou blocos SEARCH/REPLACE válidos. Resposta salva em 'failed_patch_debug.txt'")

        modified_code = original_code.replace("\r\n", "\n")
        for idx, (search_block, replace_block) in enumerate(blocks, start=1):
            search_clean = search_block.replace("\r\n", "\n").strip()
            replace_clean = replace_block.replace("\r\n", "\n")

            if search_clean in modified_code:
                modified_code = modified_code.replace(search_clean, replace_clean, 1)
                continue

            original_lines = modified_code.splitlines()
            search_lines = [l for l in search_clean.splitlines() if l.strip()]
            if not search_lines: continue

            norm_search_lines = [self._normalize_line(l) for l in search_lines]
            search_len = len(norm_search_lines)
            match_found = False

            for i in range(len(original_lines) - search_len + 1):
                window = original_lines[i : i + search_len]
                norm_window = [self._normalize_line(l) for l in window]
                if norm_window == norm_search_lines:
                    original_lines[i : i + search_len] = [replace_clean]
                    modified_code = "\n".join(original_lines)
                    match_found = True
                    break

            if not match_found:
                raise ValueError(f"Não foi possível encontrar o trecho de busca original no arquivo para o Bloco #{idx}.")
        return modified_code

    def generate_patch(self, filepath: str, error_log: str, vaccines: Any, instruction: str = None, image_paths: list = None) -> str:
        if not self.api_key:
            logging.critical("COGNITION | Chamada cognitiva abortada: API key ausente.")
            sys.exit(1)

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        with open(filepath, "r", encoding="utf-8") as f:
            current_code = f.read()

        ext = os.path.splitext(filepath)[1].lower()
        lang_map = {".ts": "typescript", ".js": "javascript", ".ex": "elixir", ".exs": "elixir", ".go": "go", ".py": "python"}
        lang = lang_map.get(ext, "python")

        prompt = f"""
        Você é o córtex cognitivo do MEA v5.8.1 AGIR. Sua missão é a edição cirúrgica de código.
        Arquivo: '{os.path.basename(filepath)}'

        INSTRUÇÃO DO ENGENHEIRO:
        {instruction or "Corrija os erros lógicos ou implemente a funcionalidade solicitada."}

        CÓDIGO ATUAL:
        ```{lang}
        {current_code}
        ```

        LOG DE ERRO / CONTEXTO SRE:
        {error_log}

        {self.get_history_of_failures(filepath)}

        REGRAS DE OURO:
        1. Responda EXCLUSIVAMENTE com blocos <<<<<<< SEARCH / ======= / >>>>>>> REPLACE.
        2. O bloco SEARCH deve ser idêntico ao código atual, incluindo espaços e chaves.
        3. Não use blocos de código Markdown (```).
        4. Sem explicações. Seja uma API de código pura.

        <<<<<<< SEARCH
        [trecho exato do arquivo atual]
        =======
        [novo código]
        >>>>>>> REPLACE
        """

        user_content = [{"type": "text", "text": prompt}]
        if image_paths:
            print(f"[+] [VISION] Processando e injetando {len(image_paths)} imagens no córtex da MEA...")
            for img_path in image_paths:
                b64_image = self._encode_image_to_base64(img_path)
                if b64_image:
                    user_content.append({
                        "type": "image_url",
                        "image_url": {"url": b64_image}
                    })

        try:
            logging.info(f"COGNITION | Solicitando patch para {os.path.basename(filepath)}...")
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": user_content}],
                temperature=0.2
            )
            raw_output = response.choices[0].message.content.strip()
            raw_output = re.sub(r'^```\w*\s*|\s*```$', '', raw_output, flags=re.MULTILINE)
            modified_full_code = self._apply_search_replace_blocks(current_code, raw_output)
            return modified_full_code
        except Exception as e:
            logging.error(f"COGNITION | Falha na reparação: {e}")
            if 'raw_output' in locals():
                with open("failed_patch_debug.txt", "w", encoding="utf-8") as f:
                    f.write(raw_output)
            raise e
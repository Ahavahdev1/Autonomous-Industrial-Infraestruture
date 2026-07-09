# mea/guardian.py
import ast
import logging
import os

class SecurityViolationError(Exception):
    """Exceção levantada quando o GuardianEngine detecta um código inseguro."""
    pass

class GuardianEngine:
    """
    O Escudo de Segurança do MEA.
    Realiza varredura de vulnerabilidades conhecidas (CVEs) e 
    práticas inseguras de desenvolvimento antes da gravação em disco.
    """
    
    # Lista de funções proibidas em código de produção
    FORBIDDEN_FUNCS = {
        'eval': 'Execução arbitrária de código',
        'exec': 'Execução arbitrária de código',
        'os.system': 'Chamada de sistema insegura',
        'subprocess.call(shell=True)': 'Injeção de comandos via shell',
        'pickle.load': 'Deserialização insegura (RCE)',
    }

    def __init__(self):
        self.logger = logging.getLogger("MEA-Guardian")

    def inspect_patch(self, code: str, filepath: str) -> tuple[bool, str]:
        """
        Analisa o patch gerado pela IA antes de ser aplicado.
        Diferencia entre Python (AST) e outras linguagens (Regex/String).
        """
        # --- SE FOR PYTHON, USA AUDITORIA AST ---
        if filepath.endswith(".py"):
            try:
                tree = ast.parse(code)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        func_name = self._get_func_name(node)
                        if func_name in self.FORBIDDEN_FUNCS:
                            return False, f"Vulnerabilidade detectada: {self.FORBIDDEN_FUNCS[func_name]}"

                    if isinstance(node, ast.keyword) and node.arg == 'shell':
                        if isinstance(node.value, ast.Constant) and node.value.value is True:
                            return False, "Uso inseguro de shell=True em subprocessos."

                return True, "Patch Python validado e seguro."
            except SyntaxError:
                return False, "Código Python com erro de sintaxe. Auditoria falhou."
            except Exception as e:
                return False, f"Erro na auditoria Python: {str(e)}"
        
        # --- SE FOR TYPESCRIPT / PRISMA / OUTROS (AUDITORIA DE TEXTO) ---
        else:
            # Verifica padrões perigosos comuns em JS/TS
            dangerous_patterns = {
                'eval(': 'Uso de eval() detectado',
                'child_process.exec(': 'Execução de comando de sistema detectada',
                'innerHTML': 'Risco potencial de XSS (Cross-Site Scripting)',
            }
            
            for pattern, reason in dangerous_patterns.items():
                if pattern in code:
                    return False, f"Vulnerabilidade detectada ({filepath}): {reason}"
            
            if not code or len(code.strip()) < 5:
                return False, "O patch gerado parece estar vazio ou corrompido."

            return True, f"Patch para {os.path.basename(filepath)} validado via varredura de texto."

    def _get_func_name(self, node: ast.Call) -> str:
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return f"{self._get_attribute_name(node.func.value)}.{node.func.attr}"
        return ""

    def _get_attribute_name(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        return ""

    def enforce(self, filepath: str, code: str):
        """
        Método principal de imposição de segurança.
        """
        # Passamos o filepath para o inspect_patch saber qual regra aplicar
        is_safe, message = self.inspect_patch(code, filepath)
        if not is_safe:
            self.logger.critical(f"GUARD-BLOCK: Tentativa de commit inseguro em {filepath}. Motivo: {message}")
            raise SecurityViolationError(message)
        
        self.logger.info(f"GUARD-PASS: Auditoria de segurança aprovada para {filepath}.")
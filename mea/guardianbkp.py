# mea/guardian.py
import ast
import logging
import os

class GuardianEngine:
    """
    O Escudo de Segurança do MEA.
    Realiza varredura de vulnerabilidades conhecidas (CVEs) e 
    práticas inseguras de desenvolvimento antes da gravação em disco.
    """
    
    # Lista de funções proibidas em código de produção (pode ser expandida via config)
    FORBIDDEN_FUNCS = {
        'eval': 'Execução arbitrária de código',
        'exec': 'Execução arbitrária de código',
        'os.system': 'Chamada de sistema insegura',
        'subprocess.call(shell=True)': 'Injeção de comandos via shell',
        'pickle.load': 'Deserialização insegura (RCE)',
    }

    def __init__(self):
        self.logger = logging.getLogger("MEA-Guardian")

    def inspect_patch(self, code: str) -> tuple[bool, str]:
        """
        Analisa o patch gerado pela IA antes de ser aplicado.
        Retorna (Sucesso, Mensagem de erro).
        """
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                # 1. Auditoria de Funções Proibidas
                if isinstance(node, ast.Call):
                    # Verifica chamadas como os.system()
                    func_name = self._get_func_name(node)
                    if func_name in self.FORBIDDEN_FUNCS:
                        return False, f"Vulnerabilidade detectada: {self.FORBIDDEN_FUNCS[func_name]}"

                # 2. Auditoria de Shell=True (Injeção de Comando)
                if isinstance(node, ast.keyword) and node.arg == 'shell':
                    if isinstance(node.value, ast.Constant) and node.value.value is True:
                        return False, "Uso inseguro de shell=True em subprocessos."

            return True, "Patch validado e seguro."
            
        except SyntaxError:
            return False, "Código com erro de sintaxe. Auditoria de segurança falhou."
        except Exception as e:
            return False, f"Erro na auditoria de segurança: {str(e)}"

    def _get_func_name(self, node: ast.Call) -> str:
        """Helper para extrair nome de função de chamadas AST."""
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
        Deve ser chamado pelo CognitionEngine.
        """
        is_safe, message = self.inspect_patch(code)
        if not is_safe:
            self.logger.critical(f"GUARD-BLOCK: Tentativa de commit inseguro em {filepath}. Motivo: {message}")
            raise SecurityViolationError(message)
        self.logger.info(f"GUARD-PASS: Audito.")
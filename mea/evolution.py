# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA — Evolutionary Adaptation Module (v5.8.1)
#  Responsável pela compatibilidade de Runtime entre eras de código.
# ==============================================================================
import os
import logging
import shutil
import stat

class EvolutionaryPatcher:
    """
    O Módulo de Adaptação. 
    Injeta vacinas sintáticas em repositórios legados para permitir execução 
    em interpretadores modernos sem falhas de API removidas.
    """

    @staticmethod
    def get_patch_payload() -> str:
        """Retorna o código de injeção que corrige Collections, AST e Warnings."""
        return (
            "\n# --- MEA EVOLUTIONARY PATCH (COLLECTIONS + AST + WARNINGS) ---\n"
            "import warnings\n"
            "warnings.filterwarnings('ignore')\n"
            "import collections, collections.abc\n"
            "for attr in ['Mapping','MutableMapping','Sequence','MutableSequence','Callable','Container','Iterable','Set','MutableSet']:\n"
            "    if not hasattr(collections, attr): setattr(collections, attr, getattr(collections.abc, attr))\n"
            "\n"
            "import ast, builtins\n"
            "class ASTConstantFixer(ast.NodeTransformer):\n"
            "    def visit_Name(self, node):\n"
            "        if node.id in ['True', 'False', 'None']: return ast.Constant(value=eval(node.id))\n"
            "        return node\n"
            "\n"
            "orig_compile = builtins.compile\n"
            "def patched_compile(source, filename, mode, flags=0, dont_inherit=False, optimize=-1, *args, **kwargs):\n"
            "    if isinstance(source, ast.AST):\n"
            "        ASTConstantFixer().visit(source)\n"
            "        ast.fix_missing_locations(source)\n"
            "    return orig_compile(source, filename, mode, flags, dont_inherit, optimize, *args, **kwargs)\n"
            "builtins.compile = patched_compile\n"
            "\n"
            "orig_import = builtins.__import__\n"
            "def patched_import(name, globals=None, locals=None, fromlist=(), level=0):\n"
            "    module = orig_import(name, globals, locals, fromlist, level)\n"
            "    if 'runtests' in name:\n"
            "        try:\n"
            "            import sys\n"
            "            rt_mod = sys.modules.get('sympy.utilities.runtests')\n"
            "            if rt_mod and hasattr(rt_mod, 'PyTestReporter'):\n"
            "                PR = getattr(rt_mod, 'PyTestReporter')\n"
            "                if not hasattr(PR, '_mea_patched'):\n"
            "                    PR._mea_patched = True\n"
            "                    orig_ex = PR.test_exception\n"
            "                    def dm(): pass\n"
            "                    def patched_ex(self, exc_info):\n"
            "                        if not hasattr(self, '_active_file'): self._active_file = 'unknown'\n"
            "                        if not hasattr(self, '_active_f'): self._active_f = dm\n"
            "                        return orig_ex(self, exc_info)\n"
            "                    PR.test_exception = patched_ex\n"
            "        except Exception: pass\n"
            "    return module\n"
            "builtins.__import__ = patched_import\n"
            "# --- END OF MEA PATCH ---\n"
        )

    @classmethod
    def apply_to_package(cls, repo_path: str, package_name: str):
        """Aplica o patch no __init__.py do projeto alvo."""
        init_file = os.path.join(repo_path, package_name, "__init__.py")
        if not os.path.exists(init_file):
            return False

        with open(init_file, "r", encoding="utf-8") as f:
            content = f.read()

        if "# --- END OF MEA PATCH ---" in content:
            return True

        print(f"[+] [EVOLUTION] Vacinando o repositório '{package_name}' para compatibilidade 3.11+...")
        
        lines = content.splitlines()
        insert_idx = 0
        for i, line in enumerate(lines):
            if "from __future__" in line:
                insert_idx = i + 1
        
        lines.insert(insert_idx, cls.get_patch_payload())
        
        with open(init_file, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return True
# -*- coding: utf-8 -*-
# ==============================================================================
#  MEA v10.6.4 "AGIR" - NÚCLEO DE EXPORTAÇÃO
# ==============================================================================
import sys
import os

# Força a raiz do projeto no path do Python
raiz = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if raiz not in sys.path:
    sys.path.insert(0, raiz)

# EXPOSIÇÃO DE MÓDULOS (Aqui reside a inteligência da colmeia)
from .chat import MEA
from .git import GitOpsManager
from .intention import IntentionBridge
from .security import SovereignGate, LogosConstitution, AgentRegistry
from .guardian import GuardianEngine
from .reliability import QuantumSREController
from .memory import MemoryProvider, JSONGibberlink
from .recon import ReconEngine
from .cognition import CognitionEngine
from .evolution import EvolutionaryPatcher
from .colmeia import SwarmOrchestrator

# Identificador de Versão de Produção
__version__ = "10.6.4-AGIR"
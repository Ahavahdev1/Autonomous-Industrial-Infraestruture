import math
import random
import logging

class QuantumSREController:
    """Gerencia a tomada de decisão usando o vetor theta de probabilidade."""
    def __init__(self):
        self.theta = math.pi / 2

    def rotate(self, success: bool, severity: float = 0.5):
        if success:
            self.theta = min(math.pi / 2, self.theta + (0.25 * (1.0 - severity)))
        else:
            self.theta = max(0.0, self.theta - (0.45 * severity))
        logging.info(f"SRE-QUANTUM | Theta rotacionado para theta={self.theta:.4f} rad")
        print(f"[~] [QUANTUM-SRE] Theta rotacionado para {self.theta:.4f} rad (~{math.degrees(self.theta):.1f}°)")

    def collapse(self) -> str:
        prob_proceed = math.sin(self.theta) ** 2
        roll = random.random()
        decisao = "PROCEED" if roll <= prob_proceed else "ROLLBACK"
        logging.info(f"SRE-QUANTUM | Colapso SRE. ProbProceed={prob_proceed*100:.1f}%, Decisão: {decisao}")
        print(f"[~] [QUANTUM-SRE] Probabilidade de PROCEED: {prob_proceed * 100:.1f}%. Sorteio: {roll * 100:.1f}%")
        return decisao
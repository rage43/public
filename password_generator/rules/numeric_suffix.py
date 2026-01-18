"""
NumericSuffixRule - Ajout de suffixes numériques
"""

from typing import Generator, List
from .base_rule import BaseRule


class NumericSuffixRule(BaseRule):
    """
    Ajoute des suffixes numériques courants.
    
    Suffixes générés (les plus utilisés statistiquement):
    - Simples: 1, 2, 3, ..., 9
    - Doubles: 11, 12, 13, 22, 23, 69, 99
    - Triples: 123, 321, 111, 000
    - Quadruples: 1234
    - Dates: 01-31 (jours du mois)
    """
    
    name = "numeric_suffix"
    description = "Suffixes numériques courants (1, 123, etc.)"
    priority = 30
    
    # Suffixes les plus courants (TOP 10 statistiquement)
    COMMON_SUFFIXES: List[str] = [
        "1", "2", "12", "123", "1234",  # Séquences
        "!!", "69", "99", "007",   # Populaires
        "01", "07",                 # Jours
    ]
    
    # Séparateurs courants
    SEPARATORS: List[str] = ["", "*", "!", "@", ".", "-"]
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations avec suffixes numériques et séparateurs."""
        for suffix in self.COMMON_SUFFIXES:
            for sep in self.SEPARATORS:
                yield password + sep + suffix
    
    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif.
        
        1 (original) + nombre de suffixes × nombre de séparateurs
        """
        return 1 + len(self.COMMON_SUFFIXES) * len(self.SEPARATORS)

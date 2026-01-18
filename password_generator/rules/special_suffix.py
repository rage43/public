"""
SpecialSuffixRule - Ajout de suffixes spéciaux
"""

from typing import Generator, List
from .base_rule import BaseRule


class SpecialSuffixRule(BaseRule):
    """
    Ajoute des suffixes avec caractères spéciaux.
    
    Suffixes générés (les plus utilisés statistiquement):
    - Simples: !, @, #, $, *
    - Composés: !!, !@, !@#, !1
    - Combinaisons courantes: 1!, 123!
    """
    
    name = "special_suffix"
    description = "Suffixes spéciaux (!, @, #, etc.)"
    priority = 40
    
    # Suffixes spéciaux les plus courants
    COMMON_SUFFIXES: List[str] = [
        # Simples
        "!", "@", "#", "$", "*", ".",
        # Doubles
        "!!", "!@", "!#", "**",
        # Composés avec chiffres (très courants)
        "1!", "!1", "123!", "!123",
        # Triple
        "!@#",
    ]
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations avec suffixes spéciaux."""
        for suffix in self.COMMON_SUFFIXES:
            yield password + suffix
    
    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif.
        
        1 (original) + nombre de suffixes
        """
        return 1 + len(self.COMMON_SUFFIXES)

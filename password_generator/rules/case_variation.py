"""
CaseVariationRule - Variations de casse (majuscules/minuscules)
"""

from typing import Generator
from .base_rule import BaseRule


class CaseVariationRule(BaseRule):
    """
    Génère des variations de casse.
    
    Variations générées (les plus courantes statistiquement):
    - Première lettre en majuscule (Password)
    - Tout en majuscules (PASSWORD)
    - Tout en minuscules (password)
    - Première et dernière lettre en majuscule (PassworD)
    """
    
    name = "case_variation"
    description = "Variations de casse (majuscule, minuscule, mixte)"
    priority = 20
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations de casse."""
        
        # 1. Première lettre en majuscule (le plus courant)
        capitalized = password.capitalize()
        if capitalized != password:
            yield capitalized
        
        # 2. Tout en majuscules
        upper = password.upper()
        if upper != password:
            yield upper
        
        # 3. Tout en minuscules
        lower = password.lower()
        if lower != password:
            yield lower
        
        # 4. Première et dernière lettre en majuscule
        if len(password) >= 2:
            first_last_upper = password[0].upper() + password[1:-1].lower() + password[-1].upper()
            if first_last_upper != password and first_last_upper not in [capitalized, upper, lower]:
                yield first_last_upper
        
        # 5. Alternance (aLtErNaTe) - moins commun mais utilisé
        alternate = ""
        for i, char in enumerate(password):
            if i % 2 == 0:
                alternate += char.lower()
            else:
                alternate += char.upper()
        
        if alternate != password and alternate not in [capitalized, upper, lower]:
            yield alternate
    
    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif.
        
        5 variations possibles (capitalize, upper, lower, first_last, alternate)
        Mais souvent certaines sont identiques à l'original
        = ~4 en moyenne
        """
        return 4

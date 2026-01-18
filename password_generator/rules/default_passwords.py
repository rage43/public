"""
DefaultPasswordsRule - Mots de passe par défaut à toujours inclure
VERSION OPTIMISÉE : Génère uniquement les variations les plus probables
"""

from typing import Generator, List
from datetime import datetime
from .base_rule import BaseRule


class DefaultPasswordsRule(BaseRule):
    """
    Ajoute les mots de passe par défaut courants avec variations MINIMALES.
    
    VERSION INTELLIGENTE:
    - TOP 10 des MDP les plus courants
    - Seulement les variations vraiment utilisées (année courante, !)
    - Évite l'explosion combinatoire
    """
    
    name = "default_passwords"
    description = "MDP par défaut (root, admin, password) - variations intelligentes"
    priority = 1  # S'exécute en premier
    enabled = True
    
    # TOP 10 mondial + admin essentiels
    DEFAULT_PASSWORDS: List[str] = [
        # Numériques (les plus courants)
        "123456",
        "12345678",
        "123456789",
        "12345",
        "1234",
        # Mots courants
        "password",
        "Password",
        "qwerty",
        "azerty",
        # Admin essentiels
        "root",
        "admin",
        "Admin",
    ]
    
    # Suffixes MINIMALISTES (les plus courants seulement)
    MINIMAL_SUFFIXES: List[str] = ["!", "1", "123"]
    
    def __init__(self):
        super().__init__()
        current_year = datetime.now().year
        # Seulement année courante et précédente
        self._years = [str(current_year), str(current_year - 1), str(current_year)[-2:]]
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """
        Génère les MDP par défaut avec variations MINIMALES.
        
        Variations générées par défaut:
        - Le MDP brut
        - MDP + année (2025, 2024, 25)
        - MDP + ! ou 1 ou 123
        """
        seen = set()
        
        for default_pwd in self.DEFAULT_PASSWORDS:
            # 1. MDP brut
            if default_pwd not in seen:
                seen.add(default_pwd)
                yield default_pwd
            
            # 2. Avec année (ex: password2025)
            for year in self._years:
                variant = default_pwd + year
                if variant not in seen:
                    seen.add(variant)
                    yield variant
            
            # 3. Avec suffixe minimal (ex: password!, password1)
            for suffix in self.MINIMAL_SUFFIXES:
                variant = default_pwd + suffix
                if variant not in seen:
                    seen.add(variant)
                    yield variant
    
    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif.
        
        12 defaults × (1 + 3 années + 3 suffixes) = 12 × 7 = 84
        Mais c'est ADDITIF (pas multiplicatif avec les autres règles)
        """
        per_default = 1 + len(self._years) + len(self.MINIMAL_SUFFIXES)
        return len(self.DEFAULT_PASSWORDS) * per_default


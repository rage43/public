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
    
    # TOP 10 mondial + admin essentiels + abréviations
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
        # Abréviations courantes (Pwd.2022, pwd1, etc.)
        "pwd",
        "Pwd",
    ]

    # Suffixes MINIMALISTES (les plus courants seulement) + "." (Pwd.)
    MINIMAL_SUFFIXES: List[str] = ["!", "1", "123", "."]

    def __init__(self):
        super().__init__()
        current_year = datetime.now().year
        # 5 dernières années en YYYY ET YY
        self._years: List[str] = []
        for offset in range(0, 5):
            y = current_year - offset
            self._years.append(str(y))           # 2026, 2025, 2024, 2023, 2022
            self._years.append(f"{y % 100:02d}") # 26, 25, 24, 23, 22

    def apply(self, password: str) -> Generator[str, None, None]:
        """
        Génère les MDP par défaut avec variations MINIMALES.

        Variations générées par défaut:
        - Le MDP brut (password, Pwd, admin...)
        - MDP + année (password2025, Pwd24, admin22)
        - MDP + suffixe (password!, Pwd1, admin.)
        - MDP + "." + année (Pwd.2022, Password.2024) -- pattern pro RH typique
        """
        seen = set()

        for default_pwd in self.DEFAULT_PASSWORDS:
            # 1. MDP brut
            if default_pwd not in seen:
                seen.add(default_pwd)
                yield default_pwd

            # 2. Avec année (ex: password2025, Pwd22)
            for year in self._years:
                variant = default_pwd + year
                if variant not in seen:
                    seen.add(variant)
                    yield variant

            # 3. Avec suffixe minimal (ex: password!, password1, password.)
            for suffix in self.MINIMAL_SUFFIXES:
                variant = default_pwd + suffix
                if variant not in seen:
                    seen.add(variant)
                    yield variant

            # 4. MDP + "." + année (Pwd.2022, Password.2024) -- très commun RH
            for year in self._years:
                variant = default_pwd + "." + year
                if variant not in seen:
                    seen.add(variant)
                    yield variant

    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif (additif, pas multiplicatif).

        14 defaults × (1 brut + 10 années + 4 suffixes + 10 années dotées)
        = 14 × 25 = 350
        """
        per_default = 1 + len(self._years) + len(self.MINIMAL_SUFFIXES) + len(self._years)
        return len(self.DEFAULT_PASSWORDS) * per_default


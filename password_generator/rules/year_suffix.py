"""
YearSuffixRule - Ajout d'années comme suffixes
VERSION OPTIMISÉE : Seulement les années les plus probables
"""

from typing import Generator, List
from datetime import datetime
from .base_rule import BaseRule


class YearSuffixRule(BaseRule):
    """
    Ajoute des années comme suffixes.
    
    VERSION INTELLIGENTE:
    - Seulement les 3 dernières années
    - Format court (25, 24, 23)
    - Pas de séparateurs multiples
    """
    
    name = "year_suffix"
    description = "Années courantes (2024, 2025)"
    priority = 50
    
    def __init__(self):
        """Initialise avec les années dynamiques."""
        super().__init__()
        current_year = datetime.now().year
        # Seulement les 3 dernières années (format long et court)
        self._suffixes = [
            str(current_year),
            str(current_year - 1),
            str(current_year - 2),
            str(current_year)[-2:],
            str(current_year - 1)[-2:],
            str(current_year - 2)[-2:],
        ]
    
    # Séparateurs limités pour les années
    SEPARATORS: List[str] = ["", "*", "!", "@", ".", "-"]
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations avec années et séparateurs."""
        for suffix in self._suffixes:
            for sep in self.SEPARATORS:
                yield password + sep + suffix
    
    def estimate_factor(self) -> int:
        """Estimation du facteur multiplicatif."""
        return 1 + len(self._suffixes) * len(self.SEPARATORS)


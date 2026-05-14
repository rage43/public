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
        # Codes département FR (grandes métropoles) : Paris, Marseille, Lyon,
        # Bordeaux, Nantes, Toulouse, Lille. Fréquents dans les MDP pro FR
        # (ex: BlcConseil;75, Martin33).
        "75", "13", "69", "33", "44", "31", "59",
    ]

    # Séparateurs courants
    # `;` et `:` ajoutés car utilisés dans les MDP pro FR (ex: Blc-Conseil;75)
    # `_` ajouté pour cohérence avec year_suffix (login style: user_123)
    SEPARATORS: List[str] = ["", "*", "!", "@", ".", "-", "_", ";", ":"]
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations avec suffixes numériques et séparateurs."""
        # Anti-double-suffix : si déjà chiffres à la fin, on saute
        # (évite "demo2024" + "1" -> "demo20241" garbage)
        if password and password[-1].isdigit():
            return

        # Early-exit longueur : suffixe minimum = 1 char (sep="" + "1")
        # Si même le plus court dépasse, on arrête.
        if len(password) + 1 > self.max_length:
            return

        max_room = self.max_length - len(password)
        for suffix in self.COMMON_SUFFIXES:
            for sep in self.SEPARATORS:
                if len(sep) + len(suffix) > max_room:
                    continue
                yield password + sep + suffix
    
    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif.
        
        1 (original) + nombre de suffixes × nombre de séparateurs
        """
        return 1 + len(self.COMMON_SUFFIXES) * len(self.SEPARATORS)

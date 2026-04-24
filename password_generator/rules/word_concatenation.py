"""
WordConcatenationRule - Concatène deux termes du fichier source
"""

from typing import Generator, List, Set, Iterable
from .base_rule import BaseRule


class WordConcatenationRule(BaseRule):
    """
    Concatène chaque mot du fichier source avec chaque autre mot.

    Cible les MDP type "cdrjuvisy" (CDR + Juvisy-sur-Orge), "martinparis",
    "projetalpha" : deux termes métier collés, sans séparateur ou avec - _ .

    ⚠️ Explosion combinatoire : keyspace = N × (N-1) × |séparateurs|.
    Pour 50 mots source : ~10 000 variantes par passe. Désactivée par défaut,
    activable via le flag CLI --concat ou dans config.json.

    Dépendance : set_words() doit être appelée avant l'exécution pour fournir
    la liste des termes à combiner (typiquement les mots du fichier source).
    """

    name = "word_concatenation"
    description = "Concatène deux mots du source (cdr + juvisy -> cdrjuvisy)"
    priority = 3  # Tôt pour que les autres règles muent le résultat concaténé
    enabled = False  # Bloat potentiel, off par défaut

    # Longueur mini d'un mot pour être combinable (évite 'a', 'de', 'le'...)
    MIN_WORD_LEN = 3

    # Séparateurs : vide (collés), underscore, tiret, point
    SEPARATORS: List[str] = ["", "_", "-", "."]

    def __init__(self):
        super().__init__()
        self._words: List[str] = []

    def set_words(self, words: Iterable[str]) -> None:
        """
        Configure la liste de mots à combiner.

        Filtre : alphabétiques >= MIN_WORD_LEN, dédupliqués, normalisés lower.
        """
        seen: Set[str] = set()
        filtered: List[str] = []
        for w in words:
            wl = w.lower().strip()
            if len(wl) < self.MIN_WORD_LEN:
                continue
            if not any(c.isalpha() for c in wl):
                continue
            if wl in seen:
                continue
            seen.add(wl)
            filtered.append(wl)
        self._words = filtered

    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les concaténations password + autre_mot."""
        if not self._words:
            return

        base = password.lower()
        for other in self._words:
            if other == base:
                continue
            for sep in self.SEPARATORS:
                yield base + sep + other

    def estimate_factor(self) -> int:
        """Facteur = 1 + (N-1) * séparateurs, sous réserve que set_words soit appelée."""
        if not self._words:
            return 1
        return 1 + max(0, len(self._words) - 1) * len(self.SEPARATORS)

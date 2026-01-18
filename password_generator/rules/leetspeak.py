"""
LeetspeakRule - Substitutions de caractères (a→4, e→3, etc.)
"""

from typing import Generator, Dict, List
from .base_rule import BaseRule


class LeetspeakRule(BaseRule):
    """
    Génère des variations leetspeak.
    
    Utilise les substitutions les plus courantes statistiquement:
    - a → 4, @
    - e → 3
    - i → 1, !
    - o → 0
    - s → $, 5
    - t → 7
    
    Pour éviter une explosion combinatoire, génère uniquement:
    1. Toutes les substitutions possibles appliquées
    2. Première lettre substituable uniquement
    """
    
    name = "leetspeak"
    description = "Substitutions leetspeak (a→4, e→3, i→1, o→0, s→$)"
    priority = 10
    
    # Substitutions les plus courantes (statistiquement)
    # Chaque caractère a une liste de substitutions possibles
    SUBSTITUTIONS: Dict[str, List[str]] = {
        'a': ['4', '@'],
        'e': ['3'],
        'i': ['1', '!'],
        'o': ['0'],
        's': ['$', '5'],
        't': ['7'],
        'l': ['1'],
        'b': ['8'],
    }
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations leetspeak."""
        lower_pwd = password.lower()
        
        # 1. Toutes les substitutions appliquées (version "full leet")
        full_leet = password
        for char, subs in self.SUBSTITUTIONS.items():
            if char in lower_pwd:
                # Utiliser la première substitution pour la version complète
                full_leet = self._replace_case_insensitive(full_leet, char, subs[0])
        
        if full_leet != password:
            yield full_leet
        
        # 2. Substitutions individuelles (les plus courantes uniquement)
        # Pour chaque caractère substituable, générer UNE variation
        for i, char in enumerate(password):
            lower_char = char.lower()
            if lower_char in self.SUBSTITUTIONS:
                # Générer avec la première substitution seulement
                sub = self.SUBSTITUTIONS[lower_char][0]
                variation = password[:i] + sub + password[i+1:]
                if variation != password and variation != full_leet:
                    yield variation
    
    def _replace_case_insensitive(self, text: str, char: str, replacement: str) -> str:
        """Remplace un caractère de manière insensible à la casse."""
        result = ""
        for c in text:
            if c.lower() == char.lower():
                result += replacement
            else:
                result += c
        return result
    
    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif.
        
        En moyenne: 1 (original) + 1 (full leet) + ~3 (variations individuelles)
        = ~5, mais arrondi à 4 car il y a souvent des doublons
        """
        return 4

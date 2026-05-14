"""
LeetspeakRule - Substitutions de caractères (a→4, e→3, etc.)
"""

from itertools import combinations
from typing import Generator, Dict, List
from .base_rule import BaseRule


class LeetspeakRule(BaseRule):
    """
    Génère des variations leetspeak.
    
    Utilise les substitutions les plus courantes statistiquement:
    - a → @, 4
    - e → 3
    - i → 1, !
    - o → 0
    - s → $, 5
    - t → 7
    - l → 1
    - b → 8

    Pour éviter une explosion combinatoire, génère :
    1. Full leet (toutes les subs avec la 1ʳᵉ option de chaque)
    2. Individual (1 sub à la fois)
    3. Partial (sous-ensembles de 2..k-1 subs simultanées, capé à k≤4 lettres
       substituables pour éviter le blow-up 2^k)
    """

    # Cap au-delà duquel on saute les partial (2^5=32 par mot + multiplié par
    # toutes les autres règles = trop). En-dessous : k=3 -> 3 partial, k=4 -> 10.
    MAX_PARTIAL_K = 4
    
    name = "leetspeak"
    description = "Substitutions leetspeak (a→@, e→3, i→1, o→0, s→$) full+individual+partial"
    priority = 10
    
    # Substitutions les plus courantes (statistiquement)
    # Chaque caractère a une liste de substitutions possibles
    SUBSTITUTIONS: Dict[str, List[str]] = {
        'a': ['@', '4'],
        'e': ['3'],
        'i': ['1', '!'],
        'o': ['0'],
        's': ['$', '5'],
        't': ['7'],
        'l': ['1'],
        'b': ['8'],
    }
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations leetspeak (full + individual + partial)."""
        lower_pwd = password.lower()

        # Positions substituables : (index, char_lower, sub_first_option)
        sub_positions = [
            (i, lower_pwd[i], self.SUBSTITUTIONS[lower_pwd[i]][0])
            for i in range(len(password))
            if lower_pwd[i] in self.SUBSTITUTIONS
        ]

        if not sub_positions:
            return

        emitted = {password}

        # 1. Full leet : toutes les subs avec la 1ʳᵉ option de chaque
        chars = list(password)
        for i, _, sub in sub_positions:
            chars[i] = sub
        full_leet = "".join(chars)
        if full_leet not in emitted:
            emitted.add(full_leet)
            yield full_leet

        # 2. Individual : 1 sub à la fois
        for i, _, sub in sub_positions:
            variation = password[:i] + sub + password[i+1:]
            if variation not in emitted:
                emitted.add(variation)
                yield variation

        # 3. Partial : sous-ensembles de taille 2..k-1, capé à k <= MAX_PARTIAL_K
        k = len(sub_positions)
        if 2 <= k <= self.MAX_PARTIAL_K:
            # range(2, k) : skip size 1 (déjà fait en 2) et size k (déjà fait en 1)
            for size in range(2, k):
                for combo in combinations(sub_positions, size):
                    chars = list(password)
                    for i, _, sub in combo:
                        chars[i] = sub
                    variation = "".join(chars)
                    if variation not in emitted:
                        emitted.add(variation)
                        yield variation
    
    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif (moyenne empirique).

        k=2: 1 full + 2 indiv = 3
        k=3: 1 full + 3 indiv + 3 partial = 7
        k=4: 1 full + 4 indiv + 10 partial = 15
        k>4: 1 full + k indiv (partial désactivé)

        Moyenne pondérée sur corpus typique (mots courts à moyens) ~= 8.
        """
        return 8

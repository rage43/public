"""
CaseComboRule - Capitalisation combinatoire bornée (1 à N lettres internes)

OPT-IN via --case-combo. Couvre les casses internes irrégulières que
CaseVariationRule (6 motifs fixes : capitalize/upper/lower/first+last/alternate/
title) ne produit PAS, par exemple la majuscule "début de syllabe" :

    wonder --(leetspeak)--> w0nd3r --(case_combo)--> W0nD3r
                                                     ^   ^
                                          maj. en positions 0 et 3 uniquement

CaseVariationRule ne génère jamais ce motif {0,3} : capitalize ne touche que
la 1ère lettre, alternate met aussi d'autres lettres en majuscule, upper met
tout. Seule une capitalisation COMBINATOIRE de k lettres arbitraires garantit
la couverture.

RÈGLE CHAÎNÉE : priorité 22, donc placée APRÈS leetspeak (10) ET
case_variation (20). Elle voit ainsi les formes leet (w0nd3r) et leur applique
les combinaisons de casse, puis ses sorties passent dans les règles de suffixe
(numeric/special/year). Un garde « n'agit que sur les formes tout-en-minuscules »
(`pwd == pwd.lower()`) évite de re-multiplier les sorties déjà capitalisées par
case_variation — sinon explosion combinatoire (case × case).

Bornes anti-blowup :
- MAX_CAPS lettres capitalisées simultanément (défaut 2 : couvre {0,3}).
- MAX_LETTERS : au-delà, la règle se désactive (les mots longs ont rarement des
  majuscules internes et le keyspace exploserait : C(15,2)=105).
"""

from itertools import combinations
from typing import Generator, List
from .base_rule import BaseRule


class CaseComboRule(BaseRule):
    """Capitalise k lettres arbitraires (k = 1..MAX_CAPS) d'une forme minuscule."""

    name = "case_combo"
    description = "Capitalisation combinatoire bornée (maj. de 1-2 lettres internes, opt-in --case-combo)"
    priority = 22  # après leetspeak (10) et case_variation (20)
    enabled = False  # OPT-IN STRICT via flag CLI uniquement

    # Nombre max de lettres capitalisées simultanément.
    # 1 -> majuscule simple (inclut capitalize). 2 -> couvre les motifs type W0nD3r.
    # 3+ -> très réaliste mais coûteux (C(L,3) variantes).
    MAX_CAPS = 2

    # Au-delà de ce nombre de LETTRES (chiffres/symboles leet exclus), on saute :
    # C(13,2)=78 variantes/mot, et les mots longs ont rarement des maj. internes.
    MAX_LETTERS = 12

    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les capitalisations combinatoires d'une forme tout-en-minuscules."""
        if not password:
            return

        # Garde : on n'agit que sur les formes SANS majuscule existante (base brute
        # + variantes leet, qui restent en minuscules). Évite de re-traiter les
        # sorties de case_variation (déjà capitalisées) -> anti-explosion case×case.
        if password != password.lower():
            return

        # Positions des lettres uniquement (les chiffres/symboles leet sont ignorés :
        # dans "w0nd3r", seules w,n,d,r sont capitalisables).
        letter_pos: List[int] = [i for i, c in enumerate(password) if c.isalpha()]
        if not letter_pos or len(letter_pos) > self.MAX_LETTERS:
            return

        emitted = {password}
        chars0 = list(password)

        for size in range(1, self.MAX_CAPS + 1):
            if size > len(letter_pos):
                break
            for combo in combinations(letter_pos, size):
                chars = list(chars0)
                for i in combo:
                    chars[i] = chars[i].upper()
                variation = "".join(chars)
                if variation not in emitted:
                    emitted.add(variation)
                    yield variation

    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif (moyenne empirique).

        Pour un mot de L lettres : sum_{k=1..MAX_CAPS} C(L, k) variantes.
        L=6, MAX_CAPS=2 : 6 + 15 = 21
        L=7, MAX_CAPS=2 : 7 + 21 = 28
        Moyenne pondérée sur corpus typique (mots courts à moyens) ~= 20.
        Ne s'applique qu'aux formes minuscules (≈ 1/6 des formes en aval de
        case_variation), mais multiplie le sous-arbre leet -> facteur effectif élevé.
        """
        return 20

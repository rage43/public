"""
AllYYRule - Suffix YYYY (1900..année_courante) ET YY (00..YY_courant)

RÈGLE ISOLÉE : ne s'enchaîne PAS avec les autres règles. Émise séparément
après la génération principale, avec sa propre déduplication interne PLUS
la dédup partagée du générateur principal.

Cible : dates de naissance (mot1969, mot80, mot1995...) extrêmement utilisées
dans les MDP personnels FR. Non activée par défaut car explose le keyspace
(~2156 variantes par mot source).

Contraintes :
- YYYY borné à [1900, année_courante] (pas de futur)
- YY borné à [00, YY_courant] (pas d'ambiguïté future, ex: 27 hors scope en 2026)
- Les YY anciens (50, 60, 70, 80, 90) sont déjà couverts par YYYY (1950..1999)
"""

from datetime import datetime
from typing import Generator, List
from .base_rule import BaseRule


class AllYYRule(BaseRule):
    """
    Génère mot + année avec les séparateurs spéciaux courants.

    Patterns par mot source (3 bases : lower + Capitalize + leet 1ère lettre) :
    - motYYYY                       (sep="" avant)
    - mot*YYYY, mot@YYYY, mot$YYYY  (sep avant)
    - motYYYY*, motYYYY@, motYYYY$  (sep après)
    - mot*YYYY@, mot!YYYY$, mot.YYYY! (paires courantes encadrantes)
    - (idem avec YY)
    - (idem avec base Capitalize : Mot...)
    - (idem avec base leet 1ère lettre : @cppav, 3xemple, !ndex, 0range, $ample)

    Année courante 2026 → 74 suffixes × 29 patterns × 3 bases = ~6438 var/mot
    worst case (avant dédup interne + cleanup). Bases réduites à 2 ou 1 si
    le mot n'a pas de 1ère lettre leetable / est déjà capitalize.
    """

    name = "all_yy"
    description = "Suffix YYYY 1900-current + YY 00-current (opt-in --all-yy)"
    priority = 99  # Pas chaînée, mais ordre logique : tout à la fin
    enabled = False  # OPT-IN STRICT via flag CLI uniquement

    # Aligné sur year_suffix pour couvrir aussi les années avec ponctuation finale.
    SEPARATORS: List[str] = ["", "*", "!", "@", "#", "$", ".", "-", "_"]

    # Paires encadrantes choisies à la main pour couvrir les combinaisons
    # courantes sans faire un produit cartésien complet des séparateurs.
    WRAPPED_SEPARATOR_PAIRS: List[tuple[str, str]] = [
        ("*", "@"),
        ("*", "!"),
        ("*", "$"),
        ("!", "@"),
        ("!", "$"),
        ("@", "!"),
        ("@", "$"),
        (".", "!"),
        (".", "@"),
        ("-", "!"),
        ("_", "!"),
        ("_", "@"),
    ]

    # Substitutions leet appliquées UNIQUEMENT sur la 1ʳᵉ lettre (alignées avec
    # LeetFirstYearRule.LEET_FIRST). Permet @cppav+1985, 3xemple+2010, etc.
    LEET_FIRST = {
        'a': '@',
        'e': '3',
        'i': '!',
        'o': '0',
        's': '$',
    }

    # Année plancher : 1980 = personne née/active en 2026 (46 ans max)
    # Modifie cette constante si tu cibles d'autres tranches d'âge.
    MIN_YEAR = 1980

    # Liste d'années importantes hors plage [MIN_YEAR, année_courante].
    # Ajoute manuellement des années spécifiques au contexte (événement,
    # anniversaire historique, etc.). Pour chaque YYYY ajoutée, le YY
    # correspondant est aussi généré automatiquement.
    # Exemples (à activer si pertinent) :
    #   IMPORTANT_YEARS = [1969, 1975, 1968]
    IMPORTANT_YEARS: List[int] = []

    def __init__(self):
        super().__init__()
        current_year = datetime.now().year
        current_yy = current_year % 100

        self._suffixes: List[str] = []
        seen: set = set()

        # 1. YYYY : MIN_YEAR → année_courante (inclusive)
        for y in range(self.MIN_YEAR, current_year + 1):
            sy = str(y)
            if sy not in seen:
                seen.add(sy)
                self._suffixes.append(sy)

        # 2. YY : 00 → YY_courant (pas de futur ambigu)
        for yy in range(0, current_yy + 1):
            yys = f"{yy:02d}"
            if yys not in seen:
                seen.add(yys)
                self._suffixes.append(yys)

        # 3. Années importantes hors plage (avec YY auto)
        for y in self.IMPORTANT_YEARS:
            sy = str(y)
            if sy not in seen:
                seen.add(sy)
                self._suffixes.append(sy)
            yys = f"{y % 100:02d}"
            if yys not in seen:
                seen.add(yys)
                self._suffixes.append(yys)

    def exclude_overlapping_suffixes(self, other_suffixes) -> int:
        """
        Retire les suffixes déjà couverts par une autre règle (typiquement
        year_suffix) pour éviter les doublons strictement redondants.

        La chaîne year_suffix + case_variation + special_suffix génère
        `mot<sep>YYYY`, `MotYYYY*`, `martinYYYY@`, etc. — soit exactement
        ce que produit all_yy pour les années overlap. Les exclure réduit
        le keyspace de ~14% sans perte de couverture.

        Args:
            other_suffixes: itérable des suffixes de l'autre règle.

        Returns:
            Nombre de suffixes retirés.
        """
        other_set = set(other_suffixes)
        before = len(self._suffixes)
        self._suffixes = [s for s in self._suffixes if s not in other_set]
        return before - len(self._suffixes)

    def apply(self, password: str) -> Generator[str, None, None]:
        """
        Génère toutes les combinaisons année pour un mot source.

        Anti-double-suffix : si déjà chiffres à la fin (mot type "demo2024"),
        on saute pour éviter "demo20241".
        """
        if not password:
            return
        if password[-1].isdigit():
            return

        max_room = self.max_length - len(password)
        if max_room < 2:  # YY = 2 chars minimum
            return

        # Bases : original + Capitalize + leet 1ère lettre (dédupliquées, ordre stable).
        lower = password.lower()
        bases: List[str] = [password]
        cap = password.capitalize()
        if cap not in bases:
            bases.append(cap)
        first = lower[0] if lower else ""
        if first in self.LEET_FIRST:
            leet_first = self.LEET_FIRST[first] + lower[1:]
            if leet_first not in bases:
                bases.append(leet_first)

        seen = set()
        for base in bases:
            for suffix in self._suffixes:
                slen = len(suffix)
                for sep in self.SEPARATORS:
                    total_len = len(sep) + slen
                    if total_len > max_room:
                        continue

                    # Pattern 1 : base + sep + année (sep avant)
                    variant = base + sep + suffix
                    if variant not in seen:
                        seen.add(variant)
                        yield variant

                    # Pattern 2 : base + année + sep (sep après)
                    # sep="" identique au pattern 1, on skip.
                    if sep == "":
                        continue
                    variant = base + suffix + sep
                    if variant not in seen:
                        seen.add(variant)
                        yield variant

                # Pattern 3 : base + sep_avant + année + sep_après
                # Liste explicite pour éviter d'exploser le keyspace avec
                # toutes les combinaisons de ponctuation possibles.
                for sep_before, sep_after in self.WRAPPED_SEPARATOR_PAIRS:
                    total_len = len(sep_before) + slen + len(sep_after)
                    if total_len > max_room:
                        continue
                    variant = base + sep_before + suffix + sep_after
                    if variant not in seen:
                        seen.add(variant)
                        yield variant

    def estimate_factor(self) -> int:
        """
        Worst case :
        len(suffixes) × ((2 × len(sep) - 1) + wrapped_pairs) × 3 bases.
        3 bases = lower + Capitalize + leet 1ère lettre (si applicable).
        2026 : 74 × 29 × 3 = 6438 (vs 4292 sans leet).
        """
        patterns = (2 * len(self.SEPARATORS) - 1) + len(self.WRAPPED_SEPARATOR_PAIRS)
        return len(self._suffixes) * patterns * 3

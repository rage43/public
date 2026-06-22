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
        # 5 dernières années en YYYY ET YY
        self._suffixes: List[str] = []
        for offset in range(0, 5):
            y = current_year - offset
            self._suffixes.append(str(y))            # 2026..2022
            self._suffixes.append(f"{y % 100:02d}")  # 26..22

    def add_extra_years(self, years) -> List[str]:
        """
        Ajoute des années fournies par l'utilisateur (CLI --years).
        Pour chaque année 4 digits, ajoute aussi sa forme YY.
        Retourne la liste des suffixes ajoutés (pour whitelist cleanup).
        """
        added = []
        for y in years:
            y = str(y).strip()
            if not y.isdigit() or len(y) != 4:
                continue
            if y not in self._suffixes:
                self._suffixes.append(y)
                added.append(y)
            yy = y[-2:]
            if yy not in self._suffixes:
                self._suffixes.append(yy)
                added.append(yy)
        return added

    def add_postal_codes(self, codes, include_department: bool = True) -> List[str]:
        """
        Ajoute des codes postaux comme suffixes (5 chiffres FR typiquement) ET,
        si include_department, leur numéro de DÉPARTEMENT (très utilisé dans les
        MDP FR : appartenance régionale, clubs, fierté locale...).

        Décomposition département (code à 5 chiffres) :
        - Métropole : 2 premiers chiffres (45770 -> 45, 75001 -> 75)
        - Outre-mer (97x/98x) : 3 premiers chiffres (97400 -> 974, 98800 -> 988)

        Accepte aussi un département seul en entrée (2-3 chiffres, ex: --postal 45).

        Retourne la liste ajoutée (pour whitelist cleanup).
        """
        added = []

        def _add(suffix: str) -> None:
            if suffix not in self._suffixes:
                self._suffixes.append(suffix)
                added.append(suffix)

        for c in codes:
            c = str(c).strip()
            if not c.isdigit() or not (2 <= len(c) <= 5):
                continue
            # Code complet (ou département seul si 2-3 chiffres fournis)
            _add(c)
            # Décomposition département pour un code postal complet (5 chiffres)
            if include_department and len(c) == 5:
                dept = c[:3] if c[:2] in ("97", "98") else c[:2]
                _add(dept)
        return added

    # Séparateurs limités pour les années
    # `;` et `:` ajoutés pour couvrir les patterns pro FR (ex: Martin;2024)
    # `_` ajouté pour couvrir le pattern "mot_année" (login style: john_2024)
    SEPARATORS: List[str] = ["", "*", "!", "@", ".", "-", "_", ";", ":"]
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations avec années et séparateurs."""
        # Anti-double-suffix : si les 4 derniers chars sont déjà des chiffres
        # (probablement déjà une année), on saute pour éviter "demo2024" + "2025".
        if len(password) >= 4 and password[-4:].isdigit():
            return

        max_room = self.max_length - len(password)
        if max_room < 2:  # plus court suffixe = "25" (YY sans sep)
            return

        for suffix in self._suffixes:
            for sep in self.SEPARATORS:
                if len(sep) + len(suffix) > max_room:
                    continue
                yield password + sep + suffix
    
    def estimate_factor(self) -> int:
        """Estimation du facteur multiplicatif."""
        return 1 + len(self._suffixes) * len(self.SEPARATORS)


"""
LeetFirstYearRule - Capitalize/leet première lettre + année + 1-3 spéciaux identiques

Pattern: {Cap | LeetFirst}{base}{year}{N×special}
Exemple pour un mot "abcdef":
  Abcdef2026, Abcdef2026*, Abcdef2026**, Abcdef2026***
  @bcdef2026, @bcdef2026*, @bcdef2026**, @bcdef2026***
"""

from datetime import datetime
from typing import Generator, List
from .base_rule import BaseRule


class LeetFirstYearRule(BaseRule):
    """
    Variations base + année + spéciaux identiques (1 à 3) à la fin.

    Variations de base:
    - Capitalize: abcdef -> Abcdef
    - Leet première lettre: a->@, e->3, i->!, o->0, s->$

    Années (auto-détectées) en formats YYYY ET YY:
    - current_year, current_year-1, current_year-2 (ex: 2026, 2025, 2024)
    - Format court 2 chiffres (ex: 26, 25, 24)
    """

    name = "leet_first_year"
    description = "Cap/leet première lettre + année (YY/YYYY) + 1-3 spéciaux identiques"
    priority = 55
    enabled = True

    # Substitutions leet uniquement sur la PREMIÈRE lettre
    LEET_FIRST = {
        'a': '@',
        'e': '3',
        'i': '!',
        'o': '0',
        's': '$',
    }

    # Caractères spéciaux à répéter à la fin (max 3 identiques)
    TRAILING_SPECIALS: List[str] = ['*', '!', '@', '#', '$', '.']

    # Nombre de répétitions du caractère spécial final (0 = pas de spécial)
    REPEAT_COUNTS: List[int] = [0, 1, 2, 3]

    def __init__(self):
        super().__init__()
        # Détection automatique de l'année en cours (YYYY + YY)
        current_year = datetime.now().year
        self.CURRENT_YEAR_FULL = current_year
        self.CURRENT_YEAR_SHORT = current_year % 100

        # Plage : année courante et 2 années précédentes, en YYYY ET YY
        self._years: List[str] = []
        for offset in range(0, 3):
            y = current_year - offset
            self._years.append(str(y))           # 2026, 2025, 2024
            self._years.append(f"{y % 100:02d}") # 26, 25, 24

    def _base_variations(self, password: str) -> List[str]:
        """Génère les variations de base (Capitalize + leet 1ère lettre)."""
        variations = []
        if not password:
            return variations

        # 1. Capitalize (Abcdef)
        cap = password[0].upper() + password[1:].lower()
        variations.append(cap)

        # 2. Leet première lettre (@bcdef) -- uniquement si la 1ère lettre est leetable
        first = password[0].lower()
        if first in self.LEET_FIRST:
            leet_first = self.LEET_FIRST[first] + password[1:].lower()
            variations.append(leet_first)

        return variations

    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations base + année + spéciaux finaux."""
        if len(password) < 2:
            return

        # Anti-double-suffix : si déjà 4 chiffres à la fin, on saute
        if len(password) >= 4 and password[-4:].isdigit():
            return

        max_len = self.max_length
        for base in self._base_variations(password):
            base_len = len(base)
            for year in self._years:
                core_len = base_len + len(year)
                if core_len > max_len:
                    continue  # même sans spéciaux, déjà trop long
                room = max_len - core_len
                for special in self.TRAILING_SPECIALS:
                    for n in self.REPEAT_COUNTS:
                        if n > room:
                            continue
                        yield base + year + (special * n)

    def estimate_factor(self) -> int:
        """
        Estimation: 2 bases × 6 années (3 YYYY + 3 YY) × 6 specials × 4 repeats
        = ~288 (mais bases dépendent de la 1ère lettre, en moyenne ~1.5)
        """
        return len(self._years) * len(self.TRAILING_SPECIALS) * len(self.REPEAT_COUNTS) * 2

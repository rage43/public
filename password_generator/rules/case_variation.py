"""
CaseVariationRule - Variations de casse (majuscules/minuscules)
"""

from typing import Generator
from .base_rule import BaseRule


class CaseVariationRule(BaseRule):
    """
    Génère des variations de casse.

    Variations générées (les plus courantes statistiquement):
    - Première lettre en majuscule (Password)
    - Tout en majuscules (PASSWORD)
    - Tout en minuscules (password)
    - Première et dernière lettre en majuscule (PassworD)
    - Alternance (pAsSwOrD)
    - Title-case par mot (Blc-Conseil, Jean-Pierre) -- uniquement si un
      séparateur de mot est présent, sinon identique à capitalize.
    """

    name = "case_variation"
    description = "Variations de casse (majuscule, minuscule, mixte, title-case)"
    priority = 20

    # Séparateurs de mots qui déclenchent la title-case (Blc-Conseil, Jean_Dupont,
    # Aix-En-Provence, O'Brien, Hello World). Sans l'un de ces caractères,
    # title-case == capitalize, on l'évite.
    WORD_SEPARATORS = "-_. '"

    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les variations de casse."""

        # 1. Première lettre en majuscule (le plus courant)
        capitalized = password.capitalize()
        if capitalized != password:
            yield capitalized

        # 2. Tout en majuscules
        upper = password.upper()
        if upper != password:
            yield upper

        # 3. Tout en minuscules
        lower = password.lower()
        if lower != password:
            yield lower

        # 4. Première et dernière lettre en majuscule
        if len(password) >= 2:
            first_last_upper = password[0].upper() + password[1:-1].lower() + password[-1].upper()
            if first_last_upper != password and first_last_upper not in [capitalized, upper, lower]:
                yield first_last_upper

        # 5. Alternance (aLtErNaTe) - moins commun mais utilisé
        alternate = ""
        for i, char in enumerate(password):
            if i % 2 == 0:
                alternate += char.lower()
            else:
                alternate += char.upper()

        if alternate != password and alternate not in [capitalized, upper, lower]:
            yield alternate

        # 6. Title-case par mot (blc-conseil -> Blc-Conseil, jean-pierre -> Jean-Pierre)
        # Déclencheur: présence d'un séparateur (-, _, ., ', espace).
        if any(sep in password for sep in self.WORD_SEPARATORS):
            title = self._title_case_by_word(password)
            if title != password and title not in [capitalized, upper, lower]:
                yield title
            # Variante "depuis lower" pour normaliser les casses sources bizarres
            # (ex: bLc-CoNsEiL -> Blc-Conseil).
            title_from_lower = self._title_case_by_word(lower)
            if title_from_lower not in [password, capitalized, upper, lower, title]:
                yield title_from_lower

    @classmethod
    def _title_case_by_word(cls, text: str) -> str:
        """
        Majuscule sur la première lettre de chaque "mot" délimité par -, _, ., ', espace.
        str.title() est évité car il ne gère pas bien les apostrophes (O'Brien -> O'Brien OK
        mais d'autres cas cassent).
        """
        result = []
        capitalize_next = True
        for ch in text:
            if ch in cls.WORD_SEPARATORS:
                result.append(ch)
                capitalize_next = True
            elif capitalize_next:
                result.append(ch.upper())
                capitalize_next = False
            else:
                result.append(ch.lower())
        return "".join(result)

    def estimate_factor(self) -> int:
        """
        Estimation du facteur multiplicatif.

        5 variations de base + 2 title-case (déclenchées si séparateur présent)
        = ~5 en moyenne (certaines sont souvent identiques à l'original)
        """
        return 5

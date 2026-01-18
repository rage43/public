"""
CombinationRule - Combine passwords with numbers found in the source file
"""

from typing import Generator, List, Set
from .base_rule import BaseRule


class CombinationRule(BaseRule):
    """
    Combine les mots de passe avec les nombres trouvés dans le fichier source.
    
    Exemples:
    - axido + 25051505 → axido25051505, Axido*25051505, @Axi*25051505!@
    - password + 2025 → password2025, Password*2025
    
    Cette règle nécessite que les nombres soient extraits en amont
    et passés via set_numbers().
    """
    
    name = "combination"
    description = "Combine MDP avec nombres du fichier (axido + 2025 → Axido*2025)"
    priority = 5  # S'exécute tôt pour créer des bases
    enabled = True
    
    def __init__(self):
        super().__init__()
        self._numbers: Set[str] = set()
    
    def set_numbers(self, numbers: Set[str]) -> None:
        """
        Configure les nombres à utiliser pour les combinaisons.
        
        Args:
            numbers: Ensemble de nombres extraits du fichier source
        """
        self._numbers = numbers
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les combinaisons avec les nombres."""
        if not self._numbers:
            return
        
        # Patterns de combinaison courants
        for num in self._numbers:
            # Basique: password + number
            yield password + num
            
            # Avec séparateurs
            yield password + "*" + num
            yield password + "_" + num
            yield password + "." + num
            
            # Version capitalisée
            cap = password.capitalize()
            if cap != password:
                yield cap + num
                yield cap + "*" + num
            
            # Style "hacker": @Pwd*Number!
            if len(password) >= 3:
                short = password[:3].capitalize()
                yield f"@{short}*{num}"
                yield f"@{short}*{num}!"
                yield f"@{short}*{num}!@"
            
            # Nombre au début aussi
            yield num + password
            yield num + "_" + password
    
    def estimate_factor(self) -> int:
        """Estimation basée sur le nombre de nombres configurés."""
        if not self._numbers:
            return 1
        # ~10 variations par nombre
        return 1 + len(self._numbers) * 10


class DuplicationRule(BaseRule):
    """
    Duplique le mot de passe.
    
    Exemples:
    - axido → axidoaxido, ax1d0ax1d0
    - test → testtest, TestTest
    """
    
    name = "duplication"
    description = "Duplication (axido → axidoaxido)"
    priority = 8
    enabled = True
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """
        Duplication intelligente : motmot ou Motmot.
        
        patterns:
        - motmot, mot*mot
        - Motmot, Mot*mot
        """
        p_lower = password.lower()
        p_cap = p_lower.capitalize()
        
        # Séparateurs limités
        separators = ["", "*"]
        
        for sep in separators:
            # mot + sep + mot (motmot, mot*mot)
            yield p_lower + sep + p_lower
            
            # Mot + sep + mot (Motmot, Mot*mot)
            yield p_cap + sep + p_lower

    def estimate_factor(self) -> int:
        return 5  # 4 variations + original


class HybridSuffixRule(BaseRule):
    """
    Génère des suffixes hybrides (lettres remplacées + chiffres).
    
    Exemples:
    - campiglia → Campigli@1, Campigli@123
    - axido → axido*25, axido*2025
    """
    
    name = "hybrid_suffix"
    description = "Suffixes hybrides (Campigli@1, axido*25)"
    priority = 35  # APRÈS numeric_suffix pour éviter le double suffixe (Campigli@1@2)
    enabled = True
    
    # Patterns de remplacement de la dernière lettre
    LETTER_REPLACEMENTS = {
        'a': ['@', '4'],
        'e': ['3'],
        'i': ['1', '!'],
        'o': ['0'],
        's': ['$', '5'],
    }
    
    # Suffixes numériques courts
    SHORT_NUMBERS = ['1', '2', '12', '123', '1!', '!1']
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les suffixes hybrides."""
        if len(password) < 2:
            return
        
        # Dernière lettre remplacée + chiffre
        last_char = password[-1].lower()
        base = password[:-1]
        
        if last_char in self.LETTER_REPLACEMENTS:
            for replacement in self.LETTER_REPLACEMENTS[last_char]:
                # Version basique
                for num in self.SHORT_NUMBERS:
                    yield base + replacement + num
                
                # Version capitalisée
                cap_base = base.capitalize()
                for num in self.SHORT_NUMBERS:
                    yield cap_base + replacement + num
    
    def estimate_factor(self) -> int:
        return 12  # Beaucoup moins de variations qu'avant (plus d'années)

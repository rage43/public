"""
Cleanup - Système de nettoyage pour filtrer les mots de passe improbables
"""

import re
from typing import List, Callable, Tuple
from abc import ABC, abstractmethod


class CleanupFilter(ABC):
    """Classe de base pour les filtres de nettoyage."""
    
    name: str = "base_filter"
    description: str = "Description du filtre"
    enabled: bool = True
    
    @abstractmethod
    def is_valid(self, password: str) -> bool:
        """
        Vérifie si le mot de passe est valide.
        
        Returns:
            True si le mot de passe doit être conservé
        """
        pass


class NoConsecutiveSpecialFilter(CleanupFilter):
    """
    Rejette les MDP avec trop de caractères spéciaux.
    
    Règles:
    - Max 2 spéciaux au début
    - Max 2 spéciaux à la fin
    - Max 2 spéciaux au milieu
    
    Exemples OK:
    - !!password (2 spéciaux début)
    - password!! (2 spéciaux fin)
    - test**2025 (2 spéciaux milieu)
    
    Exemples rejetés:
    - !!!password (3+ spéciaux début)
    - password!!! (3+ spéciaux fin)
    """
    
    name = "no_consecutive_special"
    description = "Rejette les MDP avec 3+ spéciaux consécutifs"
    
    # Caractères considérés comme spéciaux
    SPECIAL_CHARS = set("!@#$%^&*()_+-=[]{}|;':\",./<>?`~")
    
    def __init__(self, max_start: int = 2, max_end: int = 2, max_middle: int = 2):
        """
        Args:
            max_start: Nombre max de spéciaux consécutifs au début
            max_end: Nombre max de spéciaux consécutifs à la fin
            max_middle: Nombre max de spéciaux consécutifs au milieu
        """
        self.max_start = max_start
        self.max_end = max_end
        self.max_middle = max_middle
    
    def is_valid(self, password: str) -> bool:
        if not password:
            return False
        
        # Compter les spéciaux au début
        start_count = 0
        for char in password:
            if char in self.SPECIAL_CHARS:
                start_count += 1
            else:
                break
        
        if start_count > self.max_start:
            return False
        
        # Compter les spéciaux à la fin
        end_count = 0
        for char in reversed(password):
            if char in self.SPECIAL_CHARS:
                end_count += 1
            else:
                break
        
        if end_count > self.max_end:
            return False
        
        # Compter les séquences consécutives au milieu
        consecutive = 0
        for i, char in enumerate(password):
            if i == 0:
                continue  # Ignorer le début
            if char in self.SPECIAL_CHARS:
                consecutive += 1
                if consecutive > self.max_middle and i < len(password) - 1:
                    return False
            else:
                consecutive = 0
        
        return True


class NoRepeatingCharsFilter(CleanupFilter):
    """
    Rejette les MDP avec trop de caractères identiques consécutifs.
    
    Exemples rejetés:
    - passssword (5 's' consécutifs)
    - password11111 (5 '1' consécutifs)
    """
    
    name = "no_repeating_chars"
    description = "Rejette les MDP avec 5+ caractères identiques consécutifs"
    
    def __init__(self, max_repeat: int = 4):
        self.max_repeat = max_repeat
    
    def is_valid(self, password: str) -> bool:
        if len(password) < 2:
            return True
        
        count = 1
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                count += 1
                if count > self.max_repeat:
                    return False
            else:
                count = 1
        
        return True


class MinLengthFilter(CleanupFilter):
    """Rejette les MDP trop courts."""
    
    name = "min_length"
    description = "Rejette les MDP de moins de 4 caractères"
    
    def __init__(self, min_length: int = 4):
        self.min_length = min_length
    
    def is_valid(self, password: str) -> bool:
        return len(password) >= self.min_length


class MaxLengthFilter(CleanupFilter):
    """Rejette les MDP trop longs (>12 caractères)."""
    
    name = "max_length"
    description = "Rejette les MDP de plus de 12 caractères"
    
    def __init__(self, max_length: int = 12):
        self.max_length = max_length
    
    def is_valid(self, password: str) -> bool:
        return len(password) <= self.max_length


class NoOnlySpecialFilter(CleanupFilter):
    """Rejette les MDP composés uniquement de caractères spéciaux."""
    
    name = "no_only_special"
    description = "Rejette les MDP sans lettre ni chiffre"
    
    def is_valid(self, password: str) -> bool:
        return any(c.isalnum() for c in password)


class NoImprobablePatternFilter(CleanupFilter):
    """
    Rejette les patterns improbables.
    
    Patterns rejetés:
    - Que des chiffres de plus de 10 caractères (sauf dates)
    - Alternance excessive de spéciaux (a!b@c#d$)
    """
    
    name = "no_improbable_pattern"
    description = "Rejette les patterns statistiquement improbables"
    
    SPECIAL_CHARS = set("!@#$%^&*()_+-=[]{}|;':\",./<>?`~")
    
    def is_valid(self, password: str) -> bool:
        # Que des chiffres et très long
        if password.isdigit() and len(password) > 10:
            return False
        
        # Compter les alternances lettre-spécial
        alternations = 0
        for i in range(1, len(password)):
            prev_special = password[i-1] in self.SPECIAL_CHARS
            curr_special = password[i] in self.SPECIAL_CHARS
            if prev_special != curr_special and (prev_special or curr_special):
                alternations += 1
        
        # Trop d'alternances = improbable
        if alternations > len(password) * 0.6:
            return False
        
        return True


class MaxNumericFilter(CleanupFilter):
    """
    Rejette les MDP avec trop de chiffres consécutifs au début ou à la fin.
    
    Règles:
    - Max 2 chiffres au début (ex: 12password OK, 123password NON)
    - Max 4 chiffres à la fin (ex: password2025 OK, password12345 NON)
    """
    
    name = "max_numeric"
    description = "Rejette les MDP commençant par un chiffre ou trop de chiffres à la fin"
    
    def __init__(self, max_start: int = 0, max_end: int = 4):
        self.max_start = max_start
        self.max_end = max_end
    
    def is_valid(self, password: str) -> bool:
        if not password:
            return False
            
        # Compter les chiffres au début
        start_count = 0
        for char in password:
            if char.isdigit():
                start_count += 1
            else:
                break
        
        if start_count > self.max_start:
            return False
            
        # Compter les chiffres à la fin
        end_count = 0
        for char in reversed(password):
            if char.isdigit():
                end_count += 1
            else:
                break
        
        if end_count > self.max_end:
            return False
            
        return True

class RealisticYearFilter(CleanupFilter):
    """
    Vérifie que les suffixes de 4 chiffres correspondent à une année réaliste.
    
    Règle : Si le MDP finit par 4 chiffres, ils doivent être entre 1900 et 2030.
    
    Exemples:
    - password2025 -> GARDÉ (Année cohérente)
    - password1990 -> GARDÉ (Date naissance)
    - password8392 -> REJETÉ (Bruit aléatoire)
    """
    
    name = "realistic_year"
    description = "Si 4 chiffres à la fin, doit être une année (1900-2030) ou suite logique"
    
    WHITELIST = {"1234", "0000", "1111", "2222", "3333", "4444", "5555", "6666", "7777", "8888", "9999"}
    
    def __init__(self, min_year: int = 1900, max_year: int = 2030):
        self.min_year = min_year
        self.max_year = max_year
    
    def is_valid(self, password: str) -> bool:
        if len(password) < 5:  # Trop court pour avoir base + 4 chiffres
            return True
            
        # Extraire les 4 derniers caractères
        suffix = password[-4:]
        
        # Si ce sont 4 chiffres
        if suffix.isdigit():
            # Exception pour les suites courantes
            if suffix in self.WHITELIST:
                return True
                
            # Si le caractère d'avant est aussi un chiffre, c'est une suite de 5+ chiffres
            # Ce cas est déjà géré par MaxNumericFilter(max_end=4)
            # Mais assurons-nous de ne traiter que les suffixes de "4 chiffres exacts" ou on applique à tout ?
            # Appliquons à tout bloc de 4 chiffres à la fin.
            try:
                year = int(suffix)
                if year < self.min_year or year > self.max_year:
                    return False
            except ValueError:
                pass
                
        return True


class ReadableEntropyFilter(CleanupFilter):
    """
    Rejette les mots de passe imprononçables (probablement aléatoires).
    
    Règle : Si le mot ne contient que des lettres et fait > 4 caractères,
    il doit contenir au moins une voyelle (ou 'y').
    
    Exemples:
    - tr0ub4dour -> GARDÉ (contient chiffres/symboles)
    - brrrrt -> REJETÉ (que des consonnes)
    - admin -> GARDÉ
    """
    
    name = "readable_entropy"
    description = "Rejette les suites de consonnes imprononçables"
    
    VOWELS = set("aeiouyAEIOUY")
    
    def is_valid(self, password: str) -> bool:
        # Si trop court ou contient chiffres/symboles, on ignore (ce filtre ne gère que l'alpha)
        if len(password) < 4 or not password.isalpha():
            return True
            
        # Vérifier présence de voyelle
        has_vowel = any(char in self.VOWELS for char in password)
        if not has_vowel:
            return False
            
        return True

class WeakShortFilter(CleanupFilter):
    """
    Rejette les MDP faibles et courts.
    Règle : Rejette si longueur < 6 ET commence par une minuscule.
    
    Exemples:
    - test1 (5 char, minuscule) -> REJETÉ
    - Test1 (5 char, Majusiule) -> GARDÉ
    - testing (7 char) -> GARDÉ
    """
    
    name = "weak_short"
    description = "Rejette les MDP < 6 char commençant par une minuscule"
    
    def __init__(self, threshold: int = 6):
        self.threshold = threshold
    
    def is_valid(self, password: str) -> bool:
        if not password:
            return False
            
        # Si < seuil ET commence par minuscule
        # Note: islower() renvoie False pour les chiffres/symboles, donc ils sont gardés par ce filtre
        if len(password) < self.threshold and password[0].islower():
            return False
            
        return True


class CleanupManager:
    """
    Gestionnaire des filtres de nettoyage.
    
    Utilisation:
        manager = CleanupManager()
        manager.add_default_filters()
        
        # Filtrer les mots de passe
        for pwd in passwords:
            if manager.is_valid(pwd):
                yield pwd
    """
    
    def __init__(self):
        self._filters: List[CleanupFilter] = []
    
    def add_filter(self, filter: CleanupFilter) -> None:
        """Ajoute un filtre."""
        self._filters.append(filter)
    
    def add_default_filters(self) -> None:
        """Ajoute les filtres par défaut."""
        self._filters = [
            NoConsecutiveSpecialFilter(),
            NoRepeatingCharsFilter(),
            MinLengthFilter(),
            MaxLengthFilter(),
            NoOnlySpecialFilter(),
            NoImprobablePatternFilter(),
            MaxNumericFilter(),
            WeakShortFilter(),
            RealisticYearFilter(),
            ReadableEntropyFilter(),
        ]
    
    def is_valid(self, password: str) -> bool:
        """Vérifie si le mot de passe passe tous les filtres."""
        for filter in self._filters:
            if filter.enabled and not filter.is_valid(password):
                return False
        return True
    
    def filter_passwords(self, passwords: List[str]) -> Tuple[List[str], int]:
        """
        Filtre une liste de mots de passe.
        
        Returns:
            Tuple (mots de passe valides, nombre rejetés)
        """
        valid = []
        rejected = 0
        
        for pwd in passwords:
            if self.is_valid(pwd):
                valid.append(pwd)
            else:
                rejected += 1
        
        return valid, rejected
    
    def get_filters(self) -> List[CleanupFilter]:
        """Retourne la liste des filtres."""
        return self._filters

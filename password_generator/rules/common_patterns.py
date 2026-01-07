"""
CommonPatternsRule - Patterns de mots de passe les plus courants
"""

from typing import Generator, List
from datetime import datetime
from .base_rule import BaseRule


class CommonPatternsRule(BaseRule):
    """
    Génère les patterns de mots de passe les plus utilisés.
    
    Patterns courants:
    - Password*YY@ (mot + année courte + spécial)
    - PassworD17@ (dernière lettre majuscule + chiffres + spécial)
    - Password@2025 (mot + spécial + année)
    - PASSWORD1! (tout majuscule + chiffre + spécial)
    """
    
    name = "common_patterns"
    description = "Patterns courants (Password*55@, PassworD17@)"
    priority = 45
    enabled = True
    
    # Années courtes (2 chiffres)
    YEARS_SHORT = ['20', '21', '22', '23', '24', '25', '26', '93', '94', '95', '96', '97', '98', '99', '00', '01', '02', '03', '04', '05']
    
    # Chiffres simples courants
    COMMON_NUMS = ['1', '7', '13', '17', '21', '69', '77', '99']
    
    # Caractères spéciaux finaux courants
    SPECIAL_ENDINGS = ['!', '@', '#', '!@', '@!', '!!']
    
    def apply(self, password: str) -> Generator[str, None, None]:
        """Génère les patterns courants."""
        if len(password) < 2:
            return
        
        cap = password.capitalize()
        upper = password.upper()
        
        # Pattern 1: password*YY@ (mot + année courte + spécial)
        for yy in self.YEARS_SHORT:
            for sp in self.SPECIAL_ENDINGS:
                yield password + "*" + yy + sp
                yield cap + "*" + yy + sp
        
        # Pattern 2: PassworD17@ (dernière lettre majuscule + chiffres + spécial)
        last_upper = password[:-1] + password[-1].upper()
        if last_upper != password:
            for num in self.COMMON_NUMS:
                for sp in self.SPECIAL_ENDINGS:
                    yield last_upper + num + sp
            # Avec années courtes aussi
            for yy in self.YEARS_SHORT:
                for sp in ['!', '@']:
                    yield last_upper + yy + sp
        
        # Pattern 3: Password@2025 (mot + spécial + année complète)
        current_year = datetime.now().year
        for year in range(current_year - 5, current_year + 1):
            for sp in ['@', '#', '*']:
                yield cap + sp + str(year)
        
        # Pattern 4: PASSWORD1! (tout majuscule + chiffre + spécial)
        for num in ['1', '12', '123']:
            for sp in self.SPECIAL_ENDINGS:
                yield upper + num + sp
        
        # Pattern 5: password_YY (underscore + année)
        for yy in self.YEARS_SHORT:
            yield password + "_" + yy
            yield cap + "_" + yy
        
        # Pattern 6: Password!YY (spécial entre mot et année)
        for yy in self.YEARS_SHORT:
            for sp in ['!', '@', '#']:
                yield cap + sp + yy
    
    def estimate_factor(self) -> int:
        """Estimation du facteur multiplicatif."""
        # Approximation: beaucoup de variations
        return 150

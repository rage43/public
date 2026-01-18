"""
BaseRule - Classe abstraite pour toutes les règles de génération
"""

from abc import ABC, abstractmethod
from typing import Generator


class BaseRule(ABC):
    """
    Classe de base pour toutes les règles de génération.
    
    Pour créer une nouvelle règle:
    1. Créer un nouveau fichier dans le dossier rules/
    2. Hériter de BaseRule
    3. Implémenter apply() et estimate_factor()
    4. Ajouter la règle dans rules/__init__.py (AVAILABLE_RULES)
    5. Optionnel: Ajouter dans config.json pour activer/configurer
    
    Exemple:
        class MyCustomRule(BaseRule):
            name = "my_custom_rule"
            description = "Ma règle personnalisée"
            priority = 60
            
            def apply(self, password: str) -> Generator[str, None, None]:
                yield password + "_custom"
            
            def estimate_factor(self) -> int:
                return 2  # 1 original + 1 variation
    """
    
    # Attributs à surcharger dans les sous-classes
    name: str = "base_rule"
    description: str = "Description de la règle"
    enabled: bool = True
    priority: int = 50  # 0-100, les plus basses s'exécutent en premier
    
    @abstractmethod
    def apply(self, password: str) -> Generator[str, None, None]:
        """
        Génère les variations pour un mot de passe donné.
        
        IMPORTANT: Ne pas inclure le mot de passe original dans les variations.
        Le générateur s'occupe de conserver l'original.
        
        Args:
            password: Mot de passe source
            
        Yields:
            Variations du mot de passe (sans l'original)
        """
        pass
    
    @abstractmethod
    def estimate_factor(self) -> int:
        """
        Retourne le facteur multiplicatif de cette règle.
        
        Ce facteur indique combien de mots de passe seront générés
        pour chaque mot de passe en entrée (incluant l'original).
        
        Exemple:
        - Si la règle génère 3 variations + l'original = facteur 4
        - Si la règle génère 0 variations = facteur 1
        
        Returns:
            Facteur multiplicatif (minimum 1)
        """
        pass
    
    def __repr__(self) -> str:
        status = "enabled" if self.enabled else "disabled"
        return f"<{self.__class__.__name__} name='{self.name}' {status} priority={self.priority}>"

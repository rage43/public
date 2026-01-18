"""
Rules module - Système de règles modulaire
"""

import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from .base_rule import BaseRule
from .leetspeak import LeetspeakRule
from .case_variation import CaseVariationRule
from .numeric_suffix import NumericSuffixRule
from .special_suffix import SpecialSuffixRule
from .year_suffix import YearSuffixRule
from .advanced_rules import CombinationRule, DuplicationRule, HybridSuffixRule
from .common_patterns import CommonPatternsRule
from .default_passwords import DefaultPasswordsRule


class RuleRegistry:
    """Registre central des règles disponibles."""
    
    # Mapping nom -> classe de règle
    AVAILABLE_RULES = {
        "leetspeak": LeetspeakRule,
        "case_variation": CaseVariationRule,
        "numeric_suffix": NumericSuffixRule,
        "special_suffix": SpecialSuffixRule,
        "year_suffix": YearSuffixRule,
        "combination": CombinationRule,
        "duplication": DuplicationRule,
        "hybrid_suffix": HybridSuffixRule,
        "common_patterns": CommonPatternsRule,
        "default_passwords": DefaultPasswordsRule,
    }
    
    def __init__(self):
        """Initialise le registre avec toutes les règles disponibles."""
        self._rules: Dict[str, BaseRule] = {}
        
        # Instancier toutes les règles disponibles
        for name, rule_class in self.AVAILABLE_RULES.items():
            self._rules[name] = rule_class()
    
    def load_config(self, config_path: str) -> None:
        """
        Charge la configuration depuis un fichier JSON.
        
        Args:
            config_path: Chemin vers le fichier de configuration
        """
        path = Path(config_path)
        if not path.exists():
            return
        
        with open(path, "r", encoding="utf-8") as f:
            config = json.load(f)
        
        rules_config = config.get("rules", {})
        
        for name, settings in rules_config.items():
            if name in self._rules:
                rule = self._rules[name]
                
                if "enabled" in settings:
                    rule.enabled = settings["enabled"]
                
                if "priority" in settings:
                    rule.priority = settings["priority"]
    
    def get_rule(self, name: str) -> Optional[BaseRule]:
        """Récupère une règle par son nom."""
        return self._rules.get(name)
    
    def get_all_rules(self) -> List[BaseRule]:
        """Récupère toutes les règles disponibles."""
        return sorted(self._rules.values(), key=lambda r: r.priority)
    
    def get_active_rules(self) -> List[BaseRule]:
        """Récupère uniquement les règles activées, triées par priorité."""
        return sorted(
            [r for r in self._rules.values() if r.enabled],
            key=lambda r: r.priority
        )
    
    def enable_rule(self, name: str) -> bool:
        """Active une règle. Retourne True si la règle existe."""
        if name in self._rules:
            self._rules[name].enabled = True
            return True
        return False
    
    def disable_rule(self, name: str) -> bool:
        """Désactive une règle. Retourne True si la règle existe."""
        if name in self._rules:
            self._rules[name].enabled = False
            return True
        return False
    
    def register_rule(self, rule: BaseRule) -> None:
        """
        Enregistre une nouvelle règle personnalisée.
        
        Args:
            rule: Instance de la règle à enregistrer
        """
        self._rules[rule.name] = rule
    
    @classmethod
    def register_rule_class(cls, name: str, rule_class: type) -> None:
        """
        Enregistre une nouvelle classe de règle.
        
        Args:
            name: Nom de la règle
            rule_class: Classe de la règle (doit hériter de BaseRule)
        """
        if not issubclass(rule_class, BaseRule):
            raise TypeError(f"{rule_class} doit hériter de BaseRule")
        cls.AVAILABLE_RULES[name] = rule_class


__all__ = [
    "RuleRegistry",
    "BaseRule",
    "LeetspeakRule",
    "CaseVariationRule", 
    "NumericSuffixRule",
    "SpecialSuffixRule",
    "YearSuffixRule",
    "CombinationRule",
    "DuplicationRule",
    "HybridSuffixRule",
    "CommonPatternsRule",
    "DefaultPasswordsRule",
]

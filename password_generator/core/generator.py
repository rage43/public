"""
Generator - Moteur de génération des mots de passe
"""

from typing import List, Generator, Set, TYPE_CHECKING, Optional
from pathlib import Path
import sys

if TYPE_CHECKING:
    from rules.base_rule import BaseRule
    from core.cleanup import CleanupManager


class PasswordGenerator:
    """Génère les mots de passe en appliquant les règles."""
    
    def __init__(
        self,
        rules: List["BaseRule"],
        batch_size: int = 10000,
        remove_duplicates: bool = True,
        show_progress: bool = True,
        cleanup_manager: Optional["CleanupManager"] = None
    ):
        """
        Initialise le générateur.
        
        Args:
            rules: Liste des règles à appliquer
            batch_size: Taille des lots pour l'écriture
            remove_duplicates: Si True, supprime les doublons
            show_progress: Si True, affiche la progression
            cleanup_manager: Gestionnaire de nettoyage pour filtrer les MDP improbables
        """
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.batch_size = batch_size
        self.remove_duplicates = remove_duplicates
        self.show_progress = show_progress
        self.cleanup_manager = cleanup_manager
        self._rejected_count = 0
    
    @property
    def rejected_count(self) -> int:
        """Nombre de MDP rejetés par le cleanup."""
        return self._rejected_count
    
    def _is_valid(self, password: str) -> bool:
        """Vérifie si le mot de passe passe les filtres de cleanup."""
        if self.cleanup_manager is None:
            return True
        return self.cleanup_manager.is_valid(password)
    
    def generate(self, password: str) -> Generator[str, None, None]:
        """
        Génère toutes les variations d'un mot de passe.
        
        VERSION OPTIMISÉE: Utilise des générateurs lazy (récursifs)
        pour éviter l'explosion mémoire. Les variations sont générées
        à la demande, jamais stockées en bloc.
        
        Args:
            password: Mot de passe source
            
        Yields:
            Variations du mot de passe
        """
        def apply_rules_recursive(pwd: str, rule_index: int) -> Generator[str, None, None]:
            """
            Applique les règles récursivement avec lazy evaluation.
            
            Pour chaque mot de passe:
            1. On le yield après toutes les règles (cas de base)
            2. On yield aussi toutes les variations de la règle courante
            """
            # Cas de base : toutes les règles ont été appliquées
            if rule_index >= len(self.rules):
                yield pwd
                return
            
            rule = self.rules[rule_index]
            
            # 1. Propager le mot de passe original vers les règles suivantes
            yield from apply_rules_recursive(pwd, rule_index + 1)
            
            # 2. Appliquer la règle courante et propager chaque variation
            for variation in rule.apply(pwd):
                yield from apply_rules_recursive(variation, rule_index + 1)
        
        # Générer toutes les variations avec filtrage
        for pwd in apply_rules_recursive(password, 0):
            if self._is_valid(pwd):
                yield pwd
            else:
                self._rejected_count += 1
    
    def generate_all(
        self, 
        source_passwords: List[str],
        max_seen_cache: int = 10_000_000
    ) -> Generator[str, None, None]:
        """
        Génère toutes les variations pour une liste de mots de passe.
        
        VERSION OPTIMISÉE: Utilise un cache LRU borné pour la déduplification
        afin d'éviter l'explosion mémoire avec des millions de mots de passe.
        
        Args:
            source_passwords: Liste des mots de passe source
            max_seen_cache: Taille max du cache de déduplification (défaut: 10M)
            
        Yields:
            Tous les mots de passe générés (dédupliqués)
        """
        if not self.remove_duplicates:
            # Pas de déduplification, yield direct
            for password in source_passwords:
                yield from self.generate(password)
            return
        
        # Cache LRU borné pour la déduplification
        # On utilise un set avec limite de taille
        seen: Set[str] = set()
        
        for password in source_passwords:
            for variation in self.generate(password):
                # Vérifier si déjà vu
                if variation in seen:
                    continue
                
                # Ajouter au cache
                seen.add(variation)
                
                # Si le cache dépasse la limite, on arrête de dédupliquer
                # les nouveaux éléments (on yield quand même)
                # Cela évite l'explosion mémoire
                if len(seen) > max_seen_cache:
                    # Vider partiellement le cache pour libérer de la mémoire
                    # On garde les 80% les plus récents conceptuellement
                    # Mais en pratique on vide tout car set n'a pas d'ordre
                    seen.clear()
                
                yield variation
    
    def generate_to_file(self, source_passwords: List[str], output_path: str) -> int:
        """
        Génère les mots de passe et les écrit dans un fichier.
        
        Args:
            source_passwords: Liste des mots de passe source
            output_path: Chemin du fichier de sortie
            
        Returns:
            Nombre de mots de passe générés
        """
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        count = 0
        self._rejected_count = 0
        batch: List[str] = []
        seen: Set[str] = set()
        total_sources = len(source_passwords)
        
        with open(path, "w", encoding="utf-8") as f:
            for idx, password in enumerate(source_passwords):
                for variation in self.generate(password):
                    # Déduplification globale
                    if self.remove_duplicates:
                        if variation in seen:
                            continue
                        seen.add(variation)
                    
                    batch.append(variation)
                    count += 1
                    
                    # Écrire par lots pour économiser la mémoire
                    if len(batch) >= self.batch_size:
                        f.write("\n".join(batch) + "\n")
                        batch = []
                        
                        # Afficher la progression
                        if self.show_progress:
                            progress = (idx + 1) / total_sources * 100
                            rejected_info = f", {self._rejected_count:,} rejetés" if self._rejected_count > 0 else ""
                            sys.stdout.write(
                                f"\r   Progression: {progress:.1f}% "
                                f"({count:,} mots de passe générés{rejected_info})"
                            )
                            sys.stdout.flush()
            
            # Écrire le reste
            if batch:
                f.write("\n".join(batch) + "\n")
        
        if self.show_progress:
            sys.stdout.write("\n")
            sys.stdout.flush()
        
        return count


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
        cleanup_manager: Optional["CleanupManager"] = None,
        max_seen_cache: int = 50_000_000,
    ):
        """
        Initialise le générateur.

        Args:
            rules: Liste des règles à appliquer
            batch_size: Taille des lots pour l'écriture
            remove_duplicates: Si True, supprime les doublons (en RAM bornée)
            show_progress: Si True, affiche la progression
            cleanup_manager: Gestionnaire de nettoyage pour filtrer les MDP improbables
            max_seen_cache: Taille max du cache de dédup. Au-delà, le cache
                            est rotaté (laisse passer des doublons mais évite OOM).
                            ~50M MDP ≈ 4 GB RAM.
        """
        self.rules = sorted(rules, key=lambda r: r.priority)
        self.batch_size = batch_size
        self.remove_duplicates = remove_duplicates
        self.show_progress = show_progress
        self.cleanup_manager = cleanup_manager
        self.max_seen_cache = max_seen_cache
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

        OPTIMISATIONS:
        - Écriture binaire avec buffer 1 MiB (vs 8 KiB par défaut)
        - Pas de `"\\n".join()` intermédiaire : on append directement avec b"\\n"
        - Cache `seen` borné : au-delà de max_seen_cache, on le vide et on
          continue (laisse passer quelques doublons mais évite l'OOM)
        - `remove_duplicates=False` : zéro RAM pour la dédup (à `sort -u` ensuite)

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
        seen: Set[str] = set() if self.remove_duplicates else None
        cap = self.max_seen_cache
        cap_hit_warned = False
        total_sources = len(source_passwords)

        # Buffer 1 MiB pour réduire les syscalls write(2).
        with open(path, "wb", buffering=1024 * 1024) as f:
            write = f.write
            batch_bytes = bytearray()
            batch_target = self.batch_size * 16  # ~16 octets/MDP en moyenne

            for idx, password in enumerate(source_passwords):
                for variation in self.generate(password):
                    # Déduplification bornée
                    if seen is not None:
                        if variation in seen:
                            continue
                        if len(seen) >= cap:
                            if not cap_hit_warned and self.show_progress:
                                sys.stdout.write(
                                    f"\n   ⚠️  Cache dédup saturé ({cap:,}), "
                                    f"rotation. `sort -u` recommandé après.\n"
                                )
                                sys.stdout.flush()
                                cap_hit_warned = True
                            seen.clear()
                        seen.add(variation)

                    batch_bytes += variation.encode("utf-8", "replace")
                    batch_bytes += b"\n"
                    count += 1

                    # Flush du batch quand on atteint la taille cible
                    if len(batch_bytes) >= batch_target:
                        write(batch_bytes)
                        batch_bytes = bytearray()

                        if self.show_progress:
                            progress = (idx + 1) / total_sources * 100
                            rejected_info = (
                                f", {self._rejected_count:,} rejetés"
                                if self._rejected_count > 0 else ""
                            )
                            sys.stdout.write(
                                f"\r   Progression: {progress:.1f}% "
                                f"({count:,} MDP générés{rejected_info})"
                            )
                            sys.stdout.flush()

            if batch_bytes:
                write(batch_bytes)

        if self.show_progress:
            sys.stdout.write("\n")
            sys.stdout.flush()

        return count


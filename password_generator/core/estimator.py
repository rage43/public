"""
Estimator - Calcul du nombre de mots de passe et de l'espace disque
"""

from typing import List, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from rules.base_rule import BaseRule
    from core.cleanup import CleanupManager


class PasswordEstimator:
    """Estime le nombre de mots de passe et l'espace disque nécessaire."""
    
    # Seuils d'avertissement par défaut
    DEFAULT_WARN_PASSWORDS = 1_000_000
    DEFAULT_WARN_DISK_GB = 1
    DEFAULT_MAX_PASSWORDS = 10_000_000
    DEFAULT_MAX_DISK_GB = 5
    
    def __init__(
        self,
        source_passwords: List[str],
        active_rules: List["BaseRule"],
        warn_passwords: int = None,
        warn_disk_gb: float = None,
        max_passwords: int = None,
        max_disk_gb: float = None
    ):
        """
        Initialise l'estimateur.
        
        Args:
            source_passwords: Liste des mots de passe source
            active_rules: Liste des règles actives
            warn_passwords: Seuil d'avertissement pour le nombre de MDP
            warn_disk_gb: Seuil d'avertissement pour l'espace disque (GB)
            max_passwords: Limite maximale de MDP
            max_disk_gb: Limite maximale d'espace disque (GB)
        """
        self.source_passwords = source_passwords
        self.active_rules = active_rules
        self.warn_passwords = warn_passwords or self.DEFAULT_WARN_PASSWORDS
        self.warn_disk_gb = warn_disk_gb or self.DEFAULT_WARN_DISK_GB
        self.max_passwords = max_passwords or self.DEFAULT_MAX_PASSWORDS
        self.max_disk_gb = max_disk_gb or self.DEFAULT_MAX_DISK_GB
    
    def average_password_length(self) -> float:
        """Calcule la longueur moyenne des mots de passe source."""
        if not self.source_passwords:
            return 0.0
        return sum(len(p) for p in self.source_passwords) / len(self.source_passwords)
    
    def estimate_total_passwords(self) -> int:
        """
        Estime le nombre total de mots de passe qui seront générés.
        
        Le calcul prend en compte que chaque règle génère des variations
        qui s'ajoutent aux mots de passe existants (pas de multiplication).
        
        Returns:
            Estimation du nombre total de mots de passe
        """
        base_count = len(self.source_passwords)
        
        # Chaque règle génère des variations additionnelles
        # Le total est: base × (1 + factor1) × (1 + factor2) × ...
        # Mais pour être plus réaliste, on utilise une approche additive
        # car les règles génèrent souvent des doublons
        
        total_factor = 1
        for rule in self.active_rules:
            # Chaque règle multiplie le nombre de mots de passe
            # Le facteur inclut le mot de passe original (1) + les variations
            total_factor *= rule.estimate_factor()
        
        return base_count * total_factor
    
    def estimate_realistic_count(self) -> int:
        """
        Estime le nombre réaliste après filtrage (méthode HEURISTIQUE legacy).

        ⚠️ Très imprécise depuis l'ajout des early-exit dans les règles
        (max_length + anti-double-suffix). Préférer `estimate_realistic_by_sampling`
        qui mesure réellement.
        """
        raw_count = self.estimate_total_passwords()
        duplication_active = any(r.name == 'duplication' and r.enabled for r in self.active_rules)
        if duplication_active:
            return int(raw_count * 0.01)
        return int(raw_count * 0.8)

    def estimate_realistic_by_sampling(
        self,
        cleanup_manager: Optional["CleanupManager"] = None,
        sample_size: int = 3,
        max_variations_per_source: int = 500_000,
    ) -> Tuple[int, float]:
        """
        Estimation par ÉCHANTILLONNAGE : on génère réellement sur les `sample_size`
        premiers mots du fichier source, on dédupe, et on extrapole.

        Beaucoup plus précis que `estimate_realistic_count()` (qui multiplie
        des facteurs sans tenir compte des early-exit).

        Args:
            cleanup_manager: pour appliquer les filtres réels pendant la simulation
            sample_size: nombre de mots source à utiliser comme échantillon
            max_variations_per_source: cap de sécurité par mot. Au-delà, on
                arrête et on extrapole. Évite que l'estimation prenne plus
                de temps que la génération elle-même.

        Returns:
            (estimation_totale, longueur_moyenne_observée)
        """
        from core.generator import PasswordGenerator

        if not self.source_passwords:
            return 0, 0.0

        n = min(sample_size, len(self.source_passwords))
        sample = self.source_passwords[:n]

        gen = PasswordGenerator(
            self.active_rules,
            cleanup_manager=cleanup_manager,
            remove_duplicates=False,
            show_progress=False,
        )

        seen = set()
        total_chars = 0
        capped = False
        for src in sample:
            count_for_src = 0
            for variation in gen.generate(src):
                if variation not in seen:
                    seen.add(variation)
                    total_chars += len(variation)
                count_for_src += 1
                # Cap par mot : si on dépasse, on extrapole
                if count_for_src >= max_variations_per_source:
                    capped = True
                    break

        if not seen:
            return 0, 0.0

        avg_per_source = len(seen) / n
        avg_length = total_chars / len(seen)

        # Si on a capé, on multiplie par un facteur correctif (les MDP
        # filtrés au-delà du cap auraient peut-être passé le cleanup).
        # Heuristique : on suppose que le ratio observé reste valide.
        estimated_total = int(avg_per_source * len(self.source_passwords))
        return estimated_total, avg_length

    def estimate_disk_size(self) -> int:
        """
        Estime l'espace disque nécessaire en bytes.
        
        Calcul: nombre_mdp × (longueur_moyenne + 1 pour newline)
        
        Returns:
            Estimation de l'espace disque en bytes
        """
        total_passwords = self.estimate_total_passwords()
        avg_length = self.average_password_length()
        
        # On ajoute quelques caractères pour les suffixes moyens des règles
        avg_suffix_length = 2  # Estimation conservative
        
        # +1 pour le caractère de nouvelle ligne
        bytes_per_password = avg_length + avg_suffix_length + 1
        
        return int(total_passwords * bytes_per_password)
    
    def check_feasibility(
        self,
        total_passwords: Optional[int] = None,
        disk_size: Optional[int] = None,
    ) -> List[str]:
        """
        Vérifie si la génération est faisable.

        Args:
            total_passwords: si fourni, utilise cette valeur (ex: estimation
                             par échantillonnage) au lieu du worst case.
            disk_size: idem pour la taille disque.

        Returns:
            Liste des avertissements (vide si tout va bien)
        """
        warnings = []

        if total_passwords is None:
            total_passwords = self.estimate_total_passwords()
        if disk_size is None:
            disk_size = self.estimate_disk_size()
        disk_gb = disk_size / (1024 ** 3)

        if total_passwords > self.warn_passwords:
            warnings.append(
                f"Nombre élevé de mots de passe ({total_passwords:,}). "
                f"La génération peut prendre du temps."
            )

        if disk_gb > self.warn_disk_gb:
            warnings.append(
                f"Espace disque estimé élevé (~{disk_gb:.2f} GB). "
                f"Vérifiez l'espace disponible."
            )

        if total_passwords > self.max_passwords:
            warnings.append(
                f"⛔ LIMITE DÉPASSÉE: {total_passwords:,} > {self.max_passwords:,} mots de passe. "
                f"Réduisez le nombre de règles ou de mots de passe source."
            )

        if disk_gb > self.max_disk_gb:
            warnings.append(
                f"⛔ LIMITE DÉPASSÉE: ~{disk_gb:.2f} GB > {self.max_disk_gb} GB. "
                f"Réduisez le nombre de règles ou de mots de passe source."
            )

        return warnings
    
    def is_feasible(self) -> bool:
        """
        Vérifie si la génération est dans les limites acceptables.
        
        Returns:
            True si la génération est faisable
        """
        total_passwords = self.estimate_total_passwords()
        disk_gb = self.estimate_disk_size() / (1024 ** 3)
        
        return (
            total_passwords <= self.max_passwords and
            disk_gb <= self.max_disk_gb
        )

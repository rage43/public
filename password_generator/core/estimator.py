"""
Estimator - Calcul du nombre de mots de passe et de l'espace disque
"""

from typing import List, TYPE_CHECKING

if TYPE_CHECKING:
    from rules.base_rule import BaseRule


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
        Estime le nombre réaliste de mots de passe après filtrage.
        Dépendant fortement des règles actives (ex: duplication + max_length = gros rejet).
        """
        raw_count = self.estimate_total_passwords()
        
        # Vérifier si duplication est active
        duplication_active = any(r.name == 'duplication' and r.enabled for r in self.active_rules)
        
        if duplication_active:
            # La duplication double la longueur, donc le filtre max_length rejette énormément
            # Estimation conservative : 1% conservés
            return int(raw_count * 0.01)
        else:
            # Sans duplication, le taux de rejet est plus faible
            # Estimation : 80% conservés
            return int(raw_count * 0.8)

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
    
    def check_feasibility(self) -> List[str]:
        """
        Vérifie si la génération est faisable.
        
        Returns:
            Liste des avertissements (vide si tout va bien)
        """
        warnings = []
        
        total_passwords = self.estimate_total_passwords()
        disk_size = self.estimate_disk_size()
        disk_gb = disk_size / (1024 ** 3)
        
        # Vérifier les avertissements
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
        
        # Vérifier les limites
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

"""
Loader - Chargement des mots de passe source
"""

from pathlib import Path
from typing import List, Set


class PasswordLoader:
    """Charge et nettoie les mots de passe depuis un fichier."""
    
    def __init__(self, remove_duplicates: bool = True, min_length: int = 1):
        """
        Initialise le loader.
        
        Args:
            remove_duplicates: Si True, supprime les doublons
            min_length: Longueur minimale des mots de passe à conserver
        """
        self.remove_duplicates = remove_duplicates
        self.min_length = min_length
    
    def load(self, filepath: str, encoding: str = "utf-8") -> List[str]:
        """
        Charge les mots de passe depuis un fichier.
        
        Args:
            filepath: Chemin vers le fichier
            encoding: Encodage du fichier
            
        Returns:
            Liste des mots de passe nettoyés
        """
        path = Path(filepath)
        
        if not path.exists():
            raise FileNotFoundError(f"Fichier introuvable: {filepath}")
        
        passwords: List[str] = []
        seen: Set[str] = set()
        
        # Essayer plusieurs encodages si UTF-8 échoue
        encodings_to_try = [encoding, "utf-8", "latin-1", "cp1252"]
        
        for enc in encodings_to_try:
            try:
                with open(path, "r", encoding=enc) as f:
                    for line in f:
                        password = line.strip()
                        
                        # Ignorer les lignes vides et trop courtes
                        if len(password) < self.min_length:
                            continue
                        
                        # Supprimer les doublons si demandé
                        if self.remove_duplicates:
                            if password in seen:
                                continue
                            seen.add(password)
                        
                        passwords.append(password)
                
                return passwords
                
            except UnicodeDecodeError:
                continue
        
        raise ValueError(f"Impossible de décoder le fichier avec les encodages: {encodings_to_try}")
    
    def load_multiple(self, filepaths: List[str]) -> List[str]:
        """
        Charge les mots de passe depuis plusieurs fichiers.
        
        Args:
            filepaths: Liste des chemins vers les fichiers
            
        Returns:
            Liste combinée des mots de passe
        """
        all_passwords: List[str] = []
        seen: Set[str] = set()
        
        for filepath in filepaths:
            passwords = self.load(filepath)
            
            for password in passwords:
                if self.remove_duplicates:
                    if password in seen:
                        continue
                    seen.add(password)
                all_passwords.append(password)
        
        return all_passwords

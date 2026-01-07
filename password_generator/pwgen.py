#!/usr/bin/env python3
"""
PWGen - Générateur de Mots de Passe Intelligent et Modulable

Ce script télécharge automatiquement les dépendances manquantes depuis GitHub
lors de la première exécution.

Usage:
    python pwgen.py --input passwords.txt --dry-run
    python pwgen.py --input passwords.txt --output generated.txt
    python pwgen.py --list-rules
"""

import argparse
import sys
import json
import re
import os
import urllib.request
import urllib.error
from pathlib import Path
from typing import Set, List, Optional

# ============================================================================
# CONFIGURATION - Modifier cette URL selon votre dépôt GitHub
# ============================================================================
GITHUB_BASE_URL = "https://raw.githubusercontent.com/rage43/public/master/password_generator"

# Liste des fichiers requis (chemin relatif -> sera téléchargé si manquant)
REQUIRED_FILES = [
    "core/__init__.py",
    "core/cleanup.py",
    "core/estimator.py",
    "core/generator.py",
    "core/loader.py",
    "rules/__init__.py",
    "rules/base_rule.py",
    "rules/case_variation.py",
    "rules/common_patterns.py",
    "rules/default_passwords.py",
    "rules/leetspeak.py",
    "rules/numeric_suffix.py",
    "rules/special_suffix.py",
    "rules/year_suffix.py",
    "rules/advanced_rules.py",
    "config.json",
]

# ============================================================================
# BOOTSTRAP - Téléchargement automatique des dépendances
# ============================================================================

def get_script_dir() -> Path:
    """Retourne le répertoire où se trouve ce script."""
    return Path(__file__).parent.resolve()


def download_file(url: str, dest_path: Path) -> bool:
    """
    Télécharge un fichier depuis une URL.
    
    Returns:
        True si succès, False sinon
    """
    try:
        # Créer le dossier parent si nécessaire
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        print(f"   ⬇️  Téléchargement: {dest_path.name}...", end=" ", flush=True)
        
        with urllib.request.urlopen(url, timeout=30) as response:
            content = response.read()
            
        with open(dest_path, 'wb') as f:
            f.write(content)
            
        print("✓")
        return True
        
    except urllib.error.HTTPError as e:
        print(f"✗ (HTTP {e.code})")
        return False
    except urllib.error.URLError as e:
        print(f"✗ (Erreur réseau: {e.reason})")
        return False
    except Exception as e:
        print(f"✗ ({e})")
        return False


def check_and_download_dependencies() -> bool:
    """
    Vérifie et télécharge les fichiers manquants depuis GitHub.
    
    Returns:
        True si toutes les dépendances sont disponibles, False sinon
    """
    script_dir = get_script_dir()
    missing_files: List[str] = []
    
    # Identifier les fichiers manquants
    for rel_path in REQUIRED_FILES:
        full_path = script_dir / rel_path
        if not full_path.exists():
            missing_files.append(rel_path)
    
    if not missing_files:
        return True  # Tout est là !
    
    print(f"\n📦 {len(missing_files)} fichier(s) manquant(s), téléchargement depuis GitHub...")
    print(f"   Source: {GITHUB_BASE_URL}\n")
    
    failed_downloads = []
    
    for rel_path in missing_files:
        url = f"{GITHUB_BASE_URL}/{rel_path}"
        dest_path = script_dir / rel_path
        
        if not download_file(url, dest_path):
            failed_downloads.append(rel_path)
    
    if failed_downloads:
        print(f"\n❌ Échec du téléchargement de {len(failed_downloads)} fichier(s):")
        for f in failed_downloads:
            print(f"   • {f}")
        print(f"\n💡 Vérifiez l'URL du dépôt: {GITHUB_BASE_URL}")
        print("   Ou téléchargez manuellement le projet complet depuis GitHub.")
        return False
    
    print(f"\n✅ Tous les fichiers ont été téléchargés avec succès!\n")
    return True


# ============================================================================
# MAIN - Code principal (identique à l'ancien main.py)
# ============================================================================

def parse_args():
    """Parse les arguments de la ligne de commande."""
    parser = argparse.ArgumentParser(
        description="PWGen - Générateur de mots de passe intelligent et modulable",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python pwgen.py --input passwords.txt --dry-run
  python pwgen.py --input passwords.txt --output generated.txt
  python pwgen.py --input passwords.txt --config custom_config.json
  python pwgen.py --input passwords.txt --no-cleanup
        """
    )
    
    parser.add_argument(
        "-i", "--input",
        help="Fichier contenant les mots de passe source (un par ligne)"
    )
    
    parser.add_argument(
        "-o", "--output",
        default="output/generated_passwords.txt",
        help="Fichier de sortie (défaut: output/generated_passwords.txt)"
    )
    
    parser.add_argument(
        "-c", "--config",
        default="config.json",
        help="Fichier de configuration JSON (défaut: config.json)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Affiche uniquement l'estimation sans générer"
    )
    
    parser.add_argument(
        "-y", "--yes",
        action="store_true",
        help="Confirme automatiquement sans demander"
    )
    
    parser.add_argument(
        "--list-rules",
        action="store_true",
        help="Liste toutes les règles disponibles"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Désactive le filtrage des MDP improbables"
    )
    
    parser.add_argument(
        "--stdout",
        action="store_true",
        help="Affiche les MDP sur stdout (pour piping vers hashcat)"
    )
    
    parser.add_argument(
        "--update",
        action="store_true",
        help="Force le re-téléchargement de tous les fichiers depuis GitHub"
    )
    
    parser.add_argument(
        "--hashcat-help",
        action="store_true",
        help="Affiche un aide-mémoire des commandes Hashcat"
    )
    
    return parser.parse_args()


def format_size(size_bytes: int) -> str:
    """Formate une taille en bytes en format lisible."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def format_number(n: int) -> str:
    """Formate un nombre avec des séparateurs de milliers."""
    return f"{n:,}".replace(",", " ")


def extract_numbers(passwords: list) -> Set[str]:
    """
    Extrait les nombres des mots de passe pour les combinaisons.
    
    Retourne les nombres composés uniquement de chiffres (3+ caractères).
    """
    numbers = set()
    
    for pwd in passwords:
        # Si le MDP est entièrement numérique
        if pwd.isdigit() and len(pwd) >= 3:
            numbers.add(pwd)
            # Ajouter aussi les 4 derniers chiffres (comme date)
            if len(pwd) >= 4:
                numbers.add(pwd[-4:])
                numbers.add(pwd[-2:])
        
        # Extraire les séquences numériques dans le MDP
        numeric_sequences = re.findall(r'\d{3,}', pwd)
        for seq in numeric_sequences:
            numbers.add(seq)
    
    return numbers


def force_update():
    """Supprime tous les fichiers pour forcer le re-téléchargement."""
    script_dir = get_script_dir()
    deleted = 0
    
    for rel_path in REQUIRED_FILES:
        full_path = script_dir / rel_path
        if full_path.exists():
            try:
                full_path.unlink()
                deleted += 1
            except Exception:
                pass
    
    # Supprimer les dossiers __pycache__
    for pycache in script_dir.rglob("__pycache__"):
        try:
            import shutil
            shutil.rmtree(pycache)
        except Exception:
            pass
    
    print(f"🗑️  {deleted} fichier(s) supprimé(s). Re-téléchargement...")


def show_hashcat_help():
    """Affiche un aide-mémoire simple pour utiliser pwgen avec hashcat."""
    help_text = """
🔓 PWGEN + HASHCAT - AIDE RAPIDE
════════════════════════════════════════════════════════════════════════

📌 UTILISATION STANDARD (avec fichier)
──────────────────────────────────────────────────────────────────────────
  1. Générer la wordlist:
     python pwgen.py -i mes_mdp.txt -o wordlist.txt -y

  2. Lancer hashcat:
     hashcat -m <TYPE> -a 0 hashes.txt wordlist.txt

⚡ UTILISATION DIRECTE (pipe, sans fichier intermédiaire)
──────────────────────────────────────────────────────────────────────────
  python pwgen.py -i mes_mdp.txt --stdout | hashcat -m <TYPE> hashes.txt

🔢 TYPES DE HASH COURANTS (-m)
──────────────────────────────────────────────────────────────────────────
  0      MD5                    │    1000   NTLM (Windows)
  100    SHA1                   │    1800   sha512crypt ($6$, Linux)
  500    md5crypt ($1$)         │    3200   bcrypt
  1400   SHA256                 │    5600   NetNTLMv2
  1700   SHA512                 │    13100  Kerberos TGS-REP

💡 EXEMPLES CONCRETS
──────────────────────────────────────────────────────────────────────────
  # Cracker des hash MD5
  python pwgen.py -i mdp.txt --stdout | hashcat -m 0 hashes.txt

  # Cracker des hash NetNTLMv2 (capture réseau Windows)
  python pwgen.py -i mdp.txt --stdout | hashcat -m 5600 hashes.txt

  # Cracker du sha512crypt (Linux /etc/shadow)
  python pwgen.py -i mdp.txt --stdout | hashcat -m 1800 hashes.txt

  # Voir les résultats après le crack
  hashcat -m 0 hashes.txt --show

📝 VERSIONS NTLM (Windows)
──────────────────────────────────────────────────────────────────────────
  1000   NTLM (hash local, SAM/NTDS)
  5500   NetNTLMv1 (ancien, capture réseau)
  5600   NetNTLMv2 (actuel, capture réseau via Responder)
"""
    print(help_text)


def main():
    args = parse_args()
    
    # Mode hashcat-help : afficher l'aide-mémoire
    if args.hashcat_help:
        show_hashcat_help()
        return 0
    
    # Mode update : supprimer les fichiers existants
    if args.update:
        force_update()
    
    # Vérifier/télécharger les dépendances
    if not check_and_download_dependencies():
        return 1
    
    # Maintenant on peut importer les modules
    # Ajouter le répertoire du script au path
    script_dir = get_script_dir()
    sys.path.insert(0, str(script_dir))
    
    try:
        from core.loader import PasswordLoader
        from core.estimator import PasswordEstimator
        from core.generator import PasswordGenerator
        from core.cleanup import CleanupManager
        from rules import RuleRegistry
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        print("   Essayez: python pwgen.py --update")
        return 1
    
    # Initialiser le registre de règles
    registry = RuleRegistry()
    
    # Liste des règles disponibles
    if args.list_rules:
        print("\n📋 Règles disponibles:\n")
        for rule in registry.get_all_rules():
            status = "✅" if rule.enabled else "❌"
            print(f"  {status} {rule.name}")
            print(f"     └─ {rule.description}")
            print(f"        Priorité: {rule.priority}, Facteur: ×{rule.estimate_factor()}")
            print()
        return 0
    
    # Vérifier que --input est fourni
    if not args.input:
        print("❌ Erreur: L'argument --input est requis")
        print("   Utilisez --help pour plus d'informations")
        return 1
    
    # Charger les mots de passe source
    print(f"\n📂 Chargement de {args.input}...")
    loader = PasswordLoader()
    
    try:
        passwords = loader.load(args.input)
    except FileNotFoundError:
        print(f"❌ Erreur: Fichier '{args.input}' introuvable")
        return 1
    except Exception as e:
        print(f"❌ Erreur lors du chargement: {e}")
        return 1
    
    print(f"   ✓ {format_number(len(passwords))} mots de passe chargés")
    
    # Extraire les nombres pour les combinaisons
    numbers = extract_numbers(passwords)
    if numbers:
        print(f"   ✓ {len(numbers)} nombres extraits pour combinaisons")
    
    # Charger la configuration
    config_path = script_dir / args.config
    config_limits = {}
    if config_path.exists():
        registry.load_config(str(config_path))
        print(f"   ✓ Configuration chargée depuis {args.config}")
        # Charger les limites de sortie
        try:
            with open(config_path) as f:
                full_conf = json.load(f)
                config_limits = full_conf.get("output", {})
        except Exception:
            pass
    
    # Configurer les règles de combinaison avec les nombres extraits
    combination_rule = registry.get_rule("combination")
    if combination_rule and numbers:
        combination_rule.set_numbers(numbers)
    
    # Obtenir les règles actives
    active_rules = registry.get_active_rules()
    
    # CAS SPÉCIAL: DefaultPasswordsRule
    # L'utilisateur veut que cette règle soit ADDITIVE et NON MULTIPLICATIVE.
    # Elle s'ajoute à la fin de la génération, sans passer par les autres règles.
    default_rule = next((r for r in active_rules if r.name == "default_passwords"), None)
    default_passwords_cnt = 0
    
    if default_rule:
        print(f"   ✓ Règle 'default_passwords' isolée (sera ajoutée à la fin)")
        # On retire la règle pour qu'elle ne soit pas exécutée dans la boucle principale
        active_rules = [r for r in active_rules if r.name != "default_passwords"]
        # Estimation de son impact (84 environ)
        # On triche un peu sur l'appel estimate_factor car il est conçu pour être multiplicatif
        # Mais ici on veut le nombre brut généré par 1 appel
        # La règle renvoie ~84 variations uniques par design
        default_passwords_cnt = default_rule.estimate_factor()
        
    print(f"   ✓ {len(active_rules)} règles de mutation actives")
    
    # Initialiser le cleanup manager
    cleanup_manager = None
    if not args.no_cleanup:
        cleanup_manager = CleanupManager()
        cleanup_manager.add_default_filters()
        print(f"   ✓ Filtrage activé ({len(cleanup_manager.get_filters())} filtres)")
    
    # Estimation
    print("\n📊 Estimation de la génération:")
    estimator = PasswordEstimator(
        passwords, 
        active_rules,
        max_passwords=config_limits.get("max_passwords"),
        max_disk_gb=config_limits.get("max_disk_gb"),
        warn_passwords=config_limits.get("warn_passwords"),
        warn_disk_gb=config_limits.get("warn_disk_gb")
    )
    
    total_passwords = estimator.estimate_total_passwords() + default_passwords_cnt
    disk_size = estimator.estimate_disk_size() # Approximation
    avg_length = estimator.average_password_length()
    
    print(f"   • Mots de passe source: {format_number(len(passwords))}")
    print(f"   • Longueur moyenne: {avg_length:.1f} caractères")
    print(f"   • Règles actives: {len(active_rules)}")
    
    # Détail des facteurs par règle
    print("\n   Facteurs multiplicatifs:")
    for rule in active_rules:
        print(f"     └─ {rule.name}: ×{rule.estimate_factor()}")
    
    disk_gb = disk_size / (1024 * 1024 * 1024)
    disk_str = f"~{disk_gb:.2f} GB"
    if disk_gb < 1:
        disk_str = f"~{disk_gb * 1024:.2f} MB"
        
    print(f"\n   📈 Total estimé (brut): {total_passwords:,} mots de passe")
    print(f"   🎯 Total réaliste (filtré): ~{estimator.estimate_realistic_count() + default_passwords_cnt:,} mots de passe")
    print(f"   💾 Espace disque estimé: {disk_str}")
    
    if cleanup_manager:
        print("   🧹 Filtrage actif (les MDP improbables seront retirés)")
    
    # Vérifications de faisabilité
    warnings = estimator.check_feasibility()
    if warnings:
        print("\n⚠️  Avertissements:")
        for warning in warnings:
            print(f"   • {warning}")
    
    # Mode dry-run
    if args.dry_run:
        print("\n✅ Mode dry-run terminé. Aucun fichier généré.")
        return 0
    
    # Mode stdout (pour piping vers hashcat)
    if args.stdout:
        generator = PasswordGenerator(
            active_rules, 
            cleanup_manager=cleanup_manager,
            show_progress=False  # Pas de progression en mode stdout
        )
        seen = set()
        for password in passwords:
            for variation in generator.generate(password):
                if variation not in seen:
                    seen.add(variation)
                    print(variation)
        return 0
    
    # Demander confirmation
    if not args.yes:
        try:
            response = input("\n🚀 Lancer la génération ? [O/n] ").strip().lower()
            if response and response not in ['o', 'oui', 'y', 'yes', '']:
                print("❌ Génération annulée.")
                return 0
        except KeyboardInterrupt:
            print("\n❌ Génération annulée.")
            return 0
    
    # Créer le dossier de sortie si nécessaire
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Générer les mots de passe
    print(f"\n⚙️  Génération en cours...")
    generator = PasswordGenerator(active_rules, cleanup_manager=cleanup_manager)
    
    generated_count = generator.generate_to_file(passwords, str(output_path))
    
    # Génération des MDP par défaut (isolés)
    if default_rule:
        print(f"   ⚙️  Ajout des MDP par défaut ({default_passwords_cnt} variations)...")
        with open(output_path, 'a', encoding='utf-8') as f:
            # On utilise le cleanup manager pour filtrer aussi ces MDP
            for variant in default_rule.apply("dummy"):
                if cleanup_manager and not cleanup_manager.is_valid(variant):
                    generator._rejected_count += 1
                    continue
                
                f.write(variant + '\n')
                generated_count += 1
    
    # Statistiques finales
    actual_size = output_path.stat().st_size
    print(f"\n✅ Génération terminée!")
    print(f"   • Fichier: {output_path}")
    print(f"   • Mots de passe générés: {format_number(generated_count)}")
    print(f"   • Taille du fichier: {format_size(actual_size)}")
    
    if generator.rejected_count > 0:
        print(f"   • MDP filtrés (improbables): {format_number(generator.rejected_count)}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

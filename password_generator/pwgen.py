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
    "pwgen.py",  # le bootstrap lui-même : --update le remplace, le prochain run
                 # exécute la nouvelle version (le processus actuel garde l'ancien
                 # code en mémoire jusqu'à sa sortie - comportement Linux normal).
    "core/__init__.py",
    "core/assist.py",
    "core/cleanup.py",
    "core/estimator.py",
    "core/generator.py",
    "core/loader.py",
    "rules/__init__.py",
    "rules/base_rule.py",
    "rules/case_variation.py",
    "rules/default_passwords.py",
    "rules/leetspeak.py",
    "rules/numeric_suffix.py",
    "rules/special_suffix.py",
    "rules/year_suffix.py",
    "rules/advanced_rules.py",
    "rules/word_concatenation.py",
    "rules/leet_first_year.py",
    "rules/all_yy.py",
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
  python pwgen.py --hashcat-help                  # Aide pour utiliser avec hashcat

💡 SUGGESTIONS DE MOTS DE BASE:
  
  🔑 Système: admin, adm, root, user, usr, sys, config, default
  👤 Personnel: Prénoms/noms (martin, mrt), villes (paris, prs)
  🏢 Professionnel: Noms d'entreprise, projets, départements
  🎯 Courants: password, pass, pwd, welcome, secret
  📅 Dates: 2020, 2024, 123, 1234
  
  💡 Pensez aux abréviations: admin → adm, martin → mrt, password → pwd
     Exemple: avec "mrt" vous obtiendrez mrt2020, mrt*2020, mrt2020**, etc.
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

    parser.add_argument(
        "--assist",
        action="store_true",
        help="Mode interactif : pose des questions sur la cible et affiche "
             "des mots-clés contextuels à AJOUTER manuellement au fichier "
             "source. N'écrit RIEN, aucune génération. Édite core/assist.py "
             "pour personnaliser les questions/mots."
    )

    parser.add_argument(
        "--concat",
        action="store_true",
        help="Active la règle word_concatenation (combine 2 mots du source, "
             "ex: cdr + juvisy -> cdrjuvisy). Explose le keyspace, à n'activer "
             "que si le fichier source est petit et ciblé."
    )

    parser.add_argument(
        "--no-dedup",
        action="store_true",
        help="Désactive la dédup en RAM (mode fichier). Pour les très grosses "
             "générations (>50M MDP). Post-traitement recommandé : "
             "`sort -u --parallel=4 -o out.txt out.txt`."
    )

    parser.add_argument(
        "--seen-cap",
        type=int,
        default=50_000_000,
        help="Taille max du cache de dédup (défaut: 50M ≈ 4 GB RAM). "
             "Au-delà, le cache est rotaté (faux négatifs possibles)."
    )

    parser.add_argument(
        "--years",
        type=str,
        default="",
        help="Années supplémentaires (CSV, ex: 2009,1990,1985). Ajoutées en "
             "suffixe YYYY ET YY avec tous les séparateurs (ex: mot2009, "
             "mot*09, mot-1990). Injecté dans year_suffix + leet_first_year."
    )

    parser.add_argument(
        "--postal",
        type=str,
        default="",
        help="Codes postaux supplémentaires (CSV, ex: 75001,13001). Ajoutés en "
             "suffixe avec séparateurs (ex: mot75001, mot-75001). "
             "Whitelistés dans les filtres pour ne pas être rejetés."
    )

    parser.add_argument(
        "--all-yy",
        action="store_true",
        help="OPT-IN : active la règle ISOLÉE all_yy. Génère mot+YYYY (1980→année "
             "courante) ET mot+YY (00→YY courant) avec 4 séparateurs (vide, *, @, .) "
             "et 2 positions (mot@yy ET motyy@) en lower ET Capitalize. "
             "Cible dates de naissance. Explose le keyspace (~1000 var/mot). "
             "N'impacte AUCUNE autre règle. Dédup contre la génération principale."
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

    # Mode assist : questionnaire interactif pour suggérer des mots-clés.
    # Branche terminale : n'écrit rien, ne génère rien.
    if args.assist:
        # Avant de pouvoir importer core.assist, on doit s'assurer que les
        # dépendances sont là (premier lancement après bootstrap).
        if not check_and_download_dependencies():
            return 1
        script_dir = get_script_dir()
        sys.path.insert(0, str(script_dir))
        from core.assist import run_assist
        return run_assist()

    # Mode update : supprimer les fichiers existants puis re-télécharger et SORTIR
    # (l'utilisateur n'a pas demandé de génération, juste un refresh).
    if args.update:
        force_update()
        if not check_and_download_dependencies():
            return 1
        print("\n✅ Mise à jour terminée. Relance pwgen.py avec --input pour générer.")
        return 0

    # Vérifier/télécharger les dépendances (cas normal : missing only)
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
        from rules.base_rule import BaseRule
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
    cleanup_config = {}
    if config_path.exists():
        registry.load_config(str(config_path))
        print(f"   ✓ Configuration chargée depuis {args.config}")
        # Charger les limites de sortie + section cleanup
        try:
            with open(config_path) as f:
                full_conf = json.load(f)
                config_limits = full_conf.get("output", {})
                cleanup_config = full_conf.get("cleanup", {})
        except Exception:
            pass

    # Propager max_length aux règles pour court-circuit pendant la génération
    # (évite de construire un MDP qui sera ensuite rejeté par MaxLengthFilter)
    BaseRule.max_length = cleanup_config.get("max_length", 14)
    
    # Configurer les règles de combinaison avec les nombres extraits
    combination_rule = registry.get_rule("combination")
    if combination_rule and numbers:
        combination_rule.set_numbers(numbers)

    # Injection des années/codes postaux utilisateur (CLI --years / --postal)
    # Parsé ici car nécessaire AVANT add_default_filters (whitelist cleanup) et
    # AVANT l'extraction des règles actives (pour que estimate_factor soit à jour).
    extra_user_years: List[str] = []
    extra_user_postals: List[str] = []
    cleanup_extra_endings: List[str] = []
    if args.years.strip():
        extra_user_years = [y.strip() for y in args.years.split(",") if y.strip()]
        ys_rule = registry.get_rule("year_suffix")
        if ys_rule:
            added = ys_rule.add_extra_years(extra_user_years)
            cleanup_extra_endings.extend(added)
            print(f"   ✓ {len(added)} année(s) custom injectée(s) dans year_suffix")
        lfy_rule = registry.get_rule("leet_first_year")
        if lfy_rule:
            lfy_rule.add_extra_years(extra_user_years)

    if args.postal.strip():
        extra_user_postals = [p.strip() for p in args.postal.split(",") if p.strip()]
        ys_rule = registry.get_rule("year_suffix")
        if ys_rule:
            added = ys_rule.add_postal_codes(extra_user_postals)
            cleanup_extra_endings.extend(added)
            print(f"   ✓ {len(added)} code(s) postal injecté(s) dans year_suffix")

    # Activer word_concatenation via CLI si demandé + lui fournir les mots source
    concat_rule = registry.get_rule("word_concatenation")
    if concat_rule:
        if args.concat:
            registry.enable_rule("word_concatenation")
            print("   ✓ Règle 'word_concatenation' activée via --concat")
        if concat_rule.enabled:
            concat_rule.set_words(passwords)
            word_count = len(concat_rule._words)
            print(f"   ✓ {word_count} mots fournis à word_concatenation")
            if word_count >= 30:
                print(f"   ⚠️  {word_count} mots -> ~{word_count * (word_count-1) * 4:,} concaténations, keyspace risque d'exploser")

    # Activation de la règle ISOLÉE all_yy via --all-yy (jamais via config.json
    # pour éviter d'oublier qu'elle est ON). Cette règle n'est PAS chaînée avec
    # les autres : elle est émise séparément après la génération principale.
    if args.all_yy:
        registry.enable_rule("all_yy")
        ayy = registry.get_rule("all_yy")
        # Optimisation: retirer les années déjà couvertes par year_suffix
        # (qui sont chaînées avec case_variation + special_suffix → produisent
        # les mêmes MDP que all_yy pour ces années). Doit être fait APRÈS les
        # injections --years/--postal pour que year_suffix._suffixes soit final.
        ys_rule = registry.get_rule("year_suffix")
        removed = 0
        if ys_rule:
            removed = ayy.exclude_overlapping_suffixes(ys_rule._suffixes)
        print("   ✓ Règle 'all_yy' ACTIVÉE via --all-yy (isolée, non chaînée)")
        print(f"        └─ {len(ayy._suffixes)} suffixes années (après -{removed} overlap year_suffix)")
        print(f"        └─ 7 patterns × 3 bases = ~{ayy.estimate_factor()} var/mot worst case")

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

    # CAS SPÉCIAL: AllYYRule (--all-yy)
    # Règle isolée comme default_passwords MAIS itère sur les mots source
    # (mot+YY pour chaque mot du fichier d'entrée).
    all_yy_rule = next((r for r in active_rules if r.name == "all_yy"), None)
    all_yy_cnt = 0
    if all_yy_rule:
        active_rules = [r for r in active_rules if r.name != "all_yy"]
        # Estimation totale = factor × nb_mots_source
        all_yy_cnt = all_yy_rule.estimate_factor() * len(passwords)
        
    print(f"   ✓ {len(active_rules)} règles de mutation actives")
    
    # Initialiser le cleanup manager
    cleanup_manager = None
    if not args.no_cleanup:
        cleanup_manager = CleanupManager()
        cleanup_manager.add_default_filters(
            cleanup_config,
            extra_endings=cleanup_extra_endings or None,
        )
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
    
    raw_total = estimator.estimate_total_passwords() + default_passwords_cnt + all_yy_cnt
    avg_length = estimator.average_password_length()

    print(f"   • Mots de passe source: {format_number(len(passwords))}")
    print(f"   • Longueur moyenne (source): {avg_length:.1f} caractères")
    print(f"   • Règles actives: {len(active_rules)}")

    # Détail des facteurs par règle
    print("\n   Facteurs multiplicatifs (worst case, sans pruning):")
    for rule in active_rules:
        print(f"     └─ {rule.name}: ×{rule.estimate_factor()}")

    # Estimation par échantillonnage : on génère réellement sur 3 mots
    # pour avoir une estimation qui tient compte des early-exit / cleanup.
    sample_n = min(3, len(passwords))
    print(f"\n   ⏳ Échantillonnage ({sample_n} mots source)...", end=" ", flush=True)
    import time as _time
    _t0 = _time.time()
    sampled_count, sampled_avg_len = estimator.estimate_realistic_by_sampling(
        cleanup_manager=cleanup_manager,
        sample_size=sample_n,
    )
    sampled_count += default_passwords_cnt + all_yy_cnt
    print(f"✓ ({_time.time() - _t0:.1f}s)")

    # Taille disque calculée sur la longueur réellement observée
    bytes_per_pwd = sampled_avg_len + 1  # +1 pour \n
    disk_size_real = int(sampled_count * bytes_per_pwd) if sampled_count else 0

    def fmt_disk(b: int) -> str:
        gb = b / (1024 ** 3)
        if gb >= 1:
            return f"~{gb:.2f} GB"
        mb = b / (1024 ** 2)
        if mb >= 1:
            return f"~{mb:.2f} MB"
        return f"~{b / 1024:.2f} KB"

    print(f"\n   📈 Worst case (sans pruning): {raw_total:,} MDP")
    print(f"   🎯 Réel attendu (échantillonné): ~{sampled_count:,} MDP")
    print(f"   💾 Espace disque estimé: {fmt_disk(disk_size_real)}")
    if sampled_avg_len:
        print(f"   📏 Longueur moy. générée: {sampled_avg_len:.1f} caractères")

    # Pour les feasibility checks ci-dessous, on utilise le compte échantillonné
    total_passwords = sampled_count
    disk_size = disk_size_real
    
    if cleanup_manager:
        print("   🧹 Filtrage actif (les MDP improbables seront retirés)")
    
    # Vérifications de faisabilité (basées sur l'échantillonnage, pas le worst case)
    warnings = estimator.check_feasibility(
        total_passwords=total_passwords,
        disk_size=disk_size,
    )
    if warnings:
        print("\n⚠️  Avertissements:")
        for warning in warnings:
            print(f"   • {warning}")
    
    # Mode dry-run
    if args.dry_run:
        # Rappel --all-yy en dry-run (le user veut un help même en dry pour ne
        # pas oublier qu'elle est ON et son comportement).
        if all_yy_rule:
            print("\n" + "="*70)
            print("⚠️  RÈGLE SPÉCIALE --all-yy ACTIVÉE")
            print("="*70)
            print(f"   • Suffixes années      : {len(all_yy_rule._suffixes)} valeurs")
            print(f"     - YYYY {all_yy_rule.MIN_YEAR}..année_courante")
            print(f"     - YY 00..YY_courant (pas de futur)")
            print(f"     - + années importantes (édite IMPORTANT_YEARS dans all_yy.py)")
            print(f"   • Séparateurs          : {all_yy_rule.SEPARATORS}")
            print(f"   • Positions            : mot@yy ET motyy@")
            print(f"   • Bases (3)            : lower + Capitalize + leet 1ère lettre")
            print(f"                            (ex: motdepasse, Motdepasse, m0tdepasse)")
            print(f"   • Worst case           : ~{all_yy_rule.estimate_factor()} var/mot")
            print(f"   • Sur {len(passwords)} mot(s) source : ~{all_yy_cnt:,} MDP additionnels")
            print(f"   • Règle ISOLÉE         : ne s'enchaîne PAS avec les autres règles")
            print(f"   • Dédup partagée       : OK contre la génération principale (mode fichier)")

        print("\n" + "="*70)
        print("💡 SUGGESTIONS DE MOTS DE BASE:")
        print("="*70)
        print("\n🔑 Système: admin, adm, root, user, usr, sys, config, default")
        print("👤 Personnel: Prénoms/noms (martin, mrt), villes (paris, prs)")
        print("🏢 Professionnel: Noms d'entreprise, projets, départements")
        print("🎯 Courants: password, pass, pwd, welcome, secret")
        print("📅 Dates: 2020, 2024, 123, 1234")
        print("\n💡 Pensez aux abréviations: admin → adm, martin → mrt, password → pwd")
        print("   Exemple: avec \"mrt\" vous obtiendrez mrt2020, mrt*2020, mrt2020**, etc.")
        print("\n✅ Mode dry-run terminé. Aucun fichier généré.")
        return 0

    # Si --all-yy + --concat sont actifs ensemble, on étend les "sources" de
    # all_yy avec les outputs de concat. Sinon all_yy n'itèrerait que sur les
    # mots originaux et raterait Novaeblah1985, Cdrjuvisy@1990, etc.
    # Matérialisation des concats : coût mémoire mais nécessaire car all_yy
    # est isolé (ne reçoit pas l'output chaîné).
    all_yy_sources = list(passwords)
    if all_yy_rule and concat_rule and concat_rule.enabled:
        concat_count = 0
        for pwd in passwords:
            for c in concat_rule.apply(pwd):
                all_yy_sources.append(c)
                concat_count += 1
        if concat_count:
            print(f"   ↳ --all-yy va itérer sur {len(passwords)} mots source "
                  f"+ {concat_count} concats (= {len(all_yy_sources)} bases)")

    # Mode stdout (pour piping vers hashcat)
    # IMPORTANT: PAS de dédup en RAM. Hashcat gère les doublons nativement,
    # et `| sort -u` le fait sinon en streaming. Garder un `set()` ici
    # explose la RAM (~10 GB pour 500M MDP).
    if args.stdout:
        generator = PasswordGenerator(
            active_rules,
            cleanup_manager=cleanup_manager,
            show_progress=False,
            remove_duplicates=False,  # dédup déléguée à hashcat / sort -u
        )
        # Écriture directe sur stdout via buffer binaire (plus rapide que print).
        out = sys.stdout.buffer
        write = out.write
        for password in passwords:
            for variation in generator.generate(password):
                write(variation.encode("utf-8", "replace"))
                write(b"\n")

        # MDP par défaut (isolés, additifs) : émis aussi en mode --stdout
        # pour ne pas perdre Pwd.2022, admin.2024, etc. côté pipe hashcat.
        if default_rule:
            for variant in default_rule.apply("dummy"):
                if cleanup_manager and not cleanup_manager.is_valid(variant):
                    continue
                write(variant.encode("utf-8", "replace"))
                write(b"\n")

        # Règle ISOLÉE --all-yy : émise après la génération principale.
        # En --stdout pas de dédup RAM (déléguée à hashcat / sort -u).
        # Itère sur all_yy_sources (mots originaux + concats si --concat actif).
        if all_yy_rule:
            for password in all_yy_sources:
                for variant in all_yy_rule.apply(password):
                    if cleanup_manager and not cleanup_manager.is_valid(variant):
                        continue
                    write(variant.encode("utf-8", "replace"))
                    write(b"\n")

        out.flush()
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
    if args.no_dedup:
        print("   ⚠️  Dédup désactivée (--no-dedup). Pense à `sort -u` après.")
    generator = PasswordGenerator(
        active_rules,
        cleanup_manager=cleanup_manager,
        remove_duplicates=not args.no_dedup,
        max_seen_cache=args.seen_cap,
    )
    
    generated_count = generator.generate_to_file(passwords, str(output_path))

    # Génération des MDP par défaut (isolés) : via emit_isolated_to_file pour
    # partager la dédup avec la génération principale (corrige le trou de dédup
    # qui existait avant).
    if default_rule:
        print(f"   ⚙️  Ajout des MDP par défaut ({default_passwords_cnt} variations)...")
        added = generator.emit_isolated_to_file(
            default_rule, passwords, str(output_path), per_password=False
        )
        generated_count += added

    # Règle ISOLÉE --all-yy : émise après default_rule, dédup partagée.
    # Itère sur all_yy_sources = mots source + concats (si --concat actif).
    if all_yy_rule:
        print(f"   ⚙️  Ajout des MDP --all-yy ({len(all_yy_sources)} bases × ~{all_yy_rule.estimate_factor()} var)...")
        added = generator.emit_isolated_to_file(
            all_yy_rule, all_yy_sources, str(output_path), per_password=True
        )
        print(f"   ✓ --all-yy a ajouté {added:,} MDP uniques après dédup/cleanup")
        generated_count += added
    
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

# 🔐 PWGen - Générateur de Mots de Passe Intelligent

**PWGen** est un générateur de wordlists personnalisées pour le password cracking. Il applique des règles de mutation intelligentes sur une liste de mots de passe source pour générer des variations réalistes.

## ✨ Fonctionnalités

- 🚀 **Auto-téléchargement** : Téléchargez uniquement `pwgen.py`, les dépendances sont téléchargées automatiquement
- 📦 **10 règles de mutation** : Leetspeak, casse, suffixes, patterns courants, etc.
- 🎯 **Optimisé mémoire** : Générateurs lazy pour traiter des milliards de combinaisons
- 🔗 **Intégration Hashcat** : Mode `--stdout` pour pipe direct vers hashcat
- 🧹 **Filtrage intelligent** : Supprime les combinaisons improbables
- 📊 **Estimation** : Prévisualise le nombre de mots de passe avant génération

## 🚀 Installation Rapide

```bash
# Télécharger uniquement le script principal
curl -O https://raw.githubusercontent.com/rage43/public/master/password_generator/pwgen.py

# Les dépendances sont téléchargées automatiquement à la première exécution
python3 pwgen.py --help
```

## 📖 Utilisation

### Génération basique

```bash
# Estimation (dry-run)
python3 pwgen.py -i mes_passwords.txt --dry-run

# Génération vers fichier
python3 pwgen.py -i mes_passwords.txt -o wordlist.txt -y
```

### Avec Hashcat

```bash
# Pipe direct (recommandé pour les grandes wordlists)
python3 pwgen.py -i mes_passwords.txt --stdout | hashcat -m 5600 hashes.txt

# Avec fichier intermédiaire
python3 pwgen.py -i base.txt -o wordlist.txt -y
hashcat -m 5600 -a 0 hashes.txt wordlist.txt
```

### Aide-mémoire Hashcat

```bash
python3 pwgen.py --hashcat-help
```

## 🎛️ Options

| Option | Description |
|--------|-------------|
| `-i, --input FILE` | Fichier de mots de passe source (requis) |
| `-o, --output FILE` | Fichier de sortie (défaut: `output/generated_passwords.txt`) |
| `--dry-run` | Affiche l'estimation sans générer |
| `--stdout` | Envoie les MDP sur stdout (pour pipe vers hashcat) |
| `-y, --yes` | Confirme automatiquement |
| `--list-rules` | Liste les règles disponibles |
| `--no-cleanup` | Désactive le filtrage des MDP improbables |
| `--hashcat-help` | Affiche l'aide-mémoire Hashcat |
| `--update` | Force le re-téléchargement des fichiers |

## 📋 Règles de Mutation

| Règle | Description | Exemple |
|-------|-------------|---------|
| `leetspeak` | Substitutions (a→4, e→3) | password → p4ssw0rd |
| `case_variation` | Variations de casse | test → Test, TEST |
| `numeric_suffix` | Suffixes numériques | pass → pass123 |
| `special_suffix` | Suffixes spéciaux | pass → pass! |
| `year_suffix` | Années | pass → pass2024 |
| `hybrid_suffix` | Hybrides | password → Password@1 |
| `combination` | Combinaisons | pass + 2025 → pass*2025 |
| `duplication` | Duplication | test → testtest |
| `common_patterns` | Patterns courants | pass → P@ssword1! |
| `default_passwords` | MDP par défaut | - → root, admin, 123456... |

## 🔧 Configuration

Créez un fichier `config.json` pour personnaliser les règles :

```json
{
  "rules": {
    "leetspeak": { "enabled": true, "priority": 10 },
    "year_suffix": { "enabled": false },
    "default_passwords": { "enabled": true, "priority": 1 }
  }
}
```

## 🔢 Types de Hash Hashcat

| Code | Type |
|------|------|
| 0 | MD5 |
| 100 | SHA1 |
| 1000 | NTLM (local) |
| 1400 | SHA256 |
| 1800 | sha512crypt ($6$) |
| 5600 | NetNTLMv2 |
| 3200 | bcrypt |

## 📁 Structure du Projet

```
password_generator/
├── pwgen.py           # Script principal (auto-download)
├── config.json        # Configuration des règles
├── core/
│   ├── generator.py   # Moteur de génération (lazy)
│   ├── loader.py      # Chargement des fichiers
│   ├── cleanup.py     # Filtrage des MDP improbables
│   └── estimator.py   # Estimation taille/nombre
└── rules/
    ├── base_rule.py   # Classe de base
    ├── leetspeak.py
    ├── case_variation.py
    └── ...
```

## ⚡ Performance

- **Mémoire** : O(1) grâce aux générateurs lazy
- **Déduplification** : Cache LRU borné (10M entrées max)
- **Streaming** : Écriture par lots de 10 000 MDP

## 📝 Licence

MIT License

---

**Made with ❤️ for pentesters**

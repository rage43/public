"""
Mode --assist : affiche TOUTES les catégories de mots-clés avec leurs
suggestions, en couleur, sans interaction. L'utilisateur regarde la liste,
décide quelles catégories sont pertinentes pour sa cible, puis utilise
`--cible <id1,id2,...>` pour les injecter automatiquement dans le source.

Module utilisé aussi par pwgen.py via :
  - ASSIST_CATEGORIES        : data structure (éditable à la main)
  - get_keywords_for_cible() : lookup pour --cible <id>
  - list_cibles()            : liste des IDs disponibles

ÉDITER : ajoute des entrées dans ASSIST_CATEGORIES ci-dessous. Le format :
  {
      "cible": "id_court",   # utilisé par --cible <id>
      "tag": "PENTEST"|"",   # tag affiché en couleur
      "label": "titre",
      "context": "explication courte (pourquoi ces mots)",
      "keywords": [...],
  }
"""

import sys
from typing import List, Dict, Any


# ============================================================================
# DONNÉES ÉDITABLES
# ============================================================================
ASSIST_CATEGORIES: List[Dict[str, Any]] = [
    # === Catégories cible (individu / organisation) ===
    {
        "cible": "org-de-formation",
        "is_main": True,
        "includes": ["saisons"],
        "tag": "",
        "label": "Organisme de formation (CFA, école pro, CDR)",
        "context": "Acronymes métier FR très spécifiques (CDR, OPCO, CPF, AFPA). "
                   "Sessions trimestrielles -> saisons auto-incluses.",
        "keywords": [
            "cdr", "cfa", "afpa", "opco", "cpf", "formation", "stagiaire",
            "session", "module", "epcc", "afdas",
        ],
    },
    {
        "cible": "mairie",
        "is_main": True,
        "includes": ["saisons"],
        "tag": "",
        "label": "Mairie / collectivité territoriale",
        "context": "Vocabulaire administration FR (commune, EPCI, syndicat). "
                   "Saisons auto-incluses (rotation MDP fréquente en collectivité).",
        "keywords": [
            "mairie", "ville", "conseil", "epci", "syndicat", "commune",
            "communaute", "agglomeration",
        ],
    },
    {
        "cible": "pme",
        "is_main": True,
        "includes": [],
        "tag": "",
        "label": "PME / société commerciale",
        "context": "Forme juridique + raison sociale + abréviations.",
        "keywords": [
            "sarl", "sas", "sa", "eurl", "scic", "groupe", "holding",
            "societe", "entreprise",
        ],
    },
    {
        "cible": "medical",
        "is_main": True,
        "includes": [],
        "tag": "",
        "label": "Médical (cabinet, clinique, hôpital, EHPAD)",
        "context": "Vocabulaire santé FR. EHPAD/cliniques privées = MDP basiques.",
        "keywords": [
            "cabinet", "clinique", "hopital", "ehpad", "medecin", "infirmier",
            "infirmiere", "secretaire", "dr", "kine", "podo",
        ],
    },
    {
        "cible": "ecole",
        "is_main": True,
        "includes": ["saisons", "mois"],
        "tag": "",
        "label": "École / établissement scolaire",
        "context": "Établissement scolaire. Trimestres + rentrée -> saisons + mois auto.",
        "keywords": [
            "ecole", "college", "lycee", "fac", "universite", "rectorat",
            "academie", "rentree", "eleve", "prof",
        ],
    },
    {
        "cible": "asso",
        "is_main": True,
        "includes": [],
        "tag": "",
        "label": "Association / club / asso 1901",
        "context": "Format 'asso + nom', 'club + thème', abréviations courtes.",
        "keywords": [
            "asso", "association", "club", "amicale", "comite", "union",
            "federation",
        ],
    },
    {
        "cible": "perso",
        "is_main": True,
        "includes": ["villes", "prenoms"],
        "tag": "",
        "label": "Cible individuelle - mots tendres + villes + prénoms FR",
        "context": "Mots affectifs FR top 7-14 (doudou, loulou, chouchou...). "
                   "Auto-inclut villes + prénoms FR (contexte perso).",
        "keywords": [
            "doudou", "loulou", "chouchou", "mamour", "bisous", "amour",
            "jetaime", "bonjour", "soleil", "cheval", "princesse",
        ],
    },

    # === Sub-catégories : pas de flag CLI direct, auto-incluses ===
    {
        "cible": "villes",
        "is_main": False,
        "tag": "",
        "label": "Grandes villes FR (auto-inclus par --cible-perso)",
        "context": "'marseille' top 11 FR. Habitants utilisent leur ville en MDP.",
        "keywords": [
            "marseille", "paris", "lyon", "toulouse", "bordeaux", "nice",
            "lille", "nantes", "strasbourg", "rennes", "montpellier", "rouen",
        ],
    },
    {
        "cible": "prenoms",
        "is_main": False,
        "tag": "",
        "label": "Prénoms FR fréquents en MDP (auto-inclus par --cible-perso)",
        "context": "'nicolas' top 25 FR. À utiliser si prénom cible inconnu.",
        "keywords": [
            "nicolas", "julien", "thomas", "camille", "martin", "dupont",
            "lucas", "hugo", "leo", "alex", "louis", "gabriel",
        ],
    },

    # === Catégories PENTEST entreprise (main) ===
    {
        "cible": "rh",
        "is_main": True,
        "includes": ["saisons", "mois"],
        "tag": "PENTEST",
        "label": "RH / départements entreprise FR",
        "context": "compta2025, rh!, achats... Politiques rotation 30/90j "
                   "-> saisons + mois auto-incluses.",
        "keywords": [
            "compta", "comptable", "rh", "drh", "finance", "achats", "achat",
            "juridique", "marketing", "commercial", "vente", "production",
            "prod", "qualite", "hse", "logistique", "direction", "siege",
            "secretariat", "informatique", "it", "paie", "contrat",
        ],
    },
    {
        "cible": "it",
        "is_main": True,
        "includes": ["svc", "cloud", "netsec", "helpdesk"],
        "tag": "PENTEST",
        "label": "IT / sysadmin (full stack)",
        "context": "Stack MS + service accounts + cloud + équipements réseau "
                   "+ helpdesk. Auto-inclut tout l'écosystème IT.",
        "keywords": [
            "windows", "Windows", "microsoft", "office", "office365", "o365",
            "exchange", "Exchange", "sharepoint", "outlook", "teams",
            "domain", "krbtgt", "kerberos", "ldap", "dc", "root", "admin",
            "administrator", "user", "guest",
        ],
    },
    {
        "cible": "banque",
        "is_main": True,
        "includes": ["helpdesk", "saisons"],
        "tag": "PENTEST",
        "label": "Banque / assurance / finance",
        "context": "Back-office bancaire. Politique sécu stricte -> helpdesk "
                   "+ rotation saisonnière auto-incluses.",
        "keywords": [
            "banque", "credit", "agios", "compte", "epargne", "assurance",
            "mutuelle", "courtier", "conseiller", "gestionnaire", "client",
            "iban", "bic", "ca", "bnp", "lcl", "sg",
        ],
    },
    {
        "cible": "industrie",
        "is_main": True,
        "includes": ["saisons"],
        "tag": "PENTEST",
        "label": "Industrie / production / SCADA",
        "context": "Atelier, OT. MDP contraints (8 char), recyclés. Rotation "
                   "saisonnière en site industriel.",
        "keywords": [
            "usine", "atelier", "production", "qualite", "securite", "hse",
            "sst", "iso9001", "supervision", "scada", "ihm", "automate",
            "operateur", "chef",
        ],
    },
    {
        "cible": "retail",
        "is_main": True,
        "includes": ["saisons", "mois"],
        "tag": "PENTEST",
        "label": "Retail / grande distribution",
        "context": "Caissier, manager rayon. Rotation mensuelle + soldes "
                   "saisonniers -> mois + saisons auto.",
        "keywords": [
            "magasin", "caisse", "rayon", "stock", "depot", "vendeur",
            "vendeuse", "manager", "directeur", "siege", "franchise",
        ],
    },
    {
        "cible": "marque",
        "is_main": True,
        "includes": [],
        "tag": "",
        "label": "Nom commercial / marque / produit interne",
        "context": "Édite manuellement les keywords avec le nom observé chez la cible.",
        "keywords": [
            "# Ajoute ici le nom du produit/marque/projet observé",
        ],
    },

    # === Sub-catégories PENTEST : auto-incluses, pas de flag CLI direct ===
    {
        "cible": "helpdesk",
        "is_main": False,
        "tag": "PENTEST",
        "label": "Helpdesk / reset (auto-inclus par --cible-it, --cible-banque)",
        "context": "MDP après reset par IT : Welcome123, Changeme, Reset.",
        "keywords": [
            "welcome", "Welcome", "changeme", "Changeme", "reset", "Reset",
            "temp", "Temp", "bienvenue", "Bienvenue", "nouveau", "Nouveau",
            "initial",
        ],
    },
    {
        "cible": "svc",
        "is_main": False,
        "tag": "PENTEST",
        "label": "Comptes service AD (auto-inclus par --cible-it)",
        "context": "Comptes service AD, MDP rarement changé.",
        "keywords": [
            "service", "svc", "sql", "backup", "monitor", "scheduler",
            "scheduled", "report", "exchange", "sharepoint", "iis", "apache",
            "tomcat", "jenkins",
        ],
    },
    {
        "cible": "cloud",
        "is_main": False,
        "tag": "PENTEST",
        "label": "Virtualisation / cloud (auto-inclus par --cible-it)",
        "context": "Comptes admin VMware/Citrix/cloud public.",
        "keywords": [
            "vmware", "vcenter", "esxi", "vsphere", "citrix", "horizon",
            "hyperv", "aws", "azure", "gcp", "openstack", "kubernetes", "k8s",
            "docker", "nutanix",
        ],
    },
    {
        "cible": "netsec",
        "is_main": False,
        "tag": "PENTEST",
        "label": "Équipements réseau/sécu (auto-inclus par --cible-it)",
        "context": "Comptes admin switches/firewalls/NAC.",
        "keywords": [
            "cisco", "Cisco", "fortinet", "fortigate", "fortiweb", "juniper",
            "palo", "paloalto", "sophos", "watchguard", "stormshield",
            "checkpoint", "fortimanager", "panorama",
        ],
    },
    {
        "cible": "saisons",
        "is_main": False,
        "tag": "PENTEST",
        "label": "Saisons FR/EN (auto-inclus par rh, mairie, formation, ecole, banque, retail, industrie)",
        "context": "Rotation 90j -> Ete2025!, Hiver2024@... Top pattern entreprise FR.",
        "keywords": [
            "ete", "Ete", "hiver", "Hiver", "printemps", "Printemps",
            "automne", "Automne", "summer", "Summer", "winter", "Winter",
            "spring", "Spring", "autumn", "fall",
        ],
    },
    {
        "cible": "mois",
        "is_main": False,
        "tag": "PENTEST",
        "label": "Mois FR (auto-inclus par rh, ecole, retail)",
        "context": "Rotation 30j -> Janvier2025!, Mars2024@...",
        "keywords": [
            "janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet",
            "aout", "septembre", "octobre", "novembre", "decembre",
            "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin", "Juillet",
            "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
        ],
    },
    # ====================================================================
    # AJOUTE TES CATÉGORIES ICI (format identique)
    # ====================================================================
]


# ============================================================================
# COULEURS ANSI (auto-disabled si stdout n'est pas un terminal)
# ============================================================================
_USE_COLOR = sys.stdout.isatty()


def _c(code: str, text: str) -> str:
    """Wrap text in ANSI color code if terminal supports it."""
    return f"\033[{code}m{text}\033[0m" if _USE_COLOR else text


def _bold(t: str) -> str:    return _c("1", t)
def _dim(t: str) -> str:     return _c("2", t)
def _red(t: str) -> str:     return _c("1;31", t)
def _green(t: str) -> str:   return _c("1;32", t)
def _yellow(t: str) -> str:  return _c("1;33", t)
def _blue(t: str) -> str:    return _c("1;34", t)
def _cyan(t: str) -> str:    return _c("1;36", t)


# ============================================================================
# HELPERS (utilisés par pwgen.py pour --cible)
# ============================================================================
def get_keywords_for_cible(cible_id: str) -> List[str]:
    """Retourne la liste des mots-clés pour un ID de cible. Vide si inconnu."""
    cible_id = cible_id.strip().lower()
    for cat in ASSIST_CATEGORIES:
        if cat["cible"] == cible_id:
            # Filtre les lignes commentées (commencent par #)
            return [k for k in cat["keywords"] if not k.startswith("#")]
    return []


def list_cibles() -> List[str]:
    """Retourne tous les IDs cible disponibles (pour --help / validation)."""
    return [cat["cible"] for cat in ASSIST_CATEGORIES]


# ============================================================================
# AFFICHAGE
# ============================================================================
def run_assist() -> int:
    """
    Affiche TOUTES les catégories avec leurs mots-clés en couleur.
    Pas d'interaction : l'utilisateur lit, puis utilise --cible <id>.
    """
    print()
    print(_bold(_cyan("=" * 70)))
    print(_bold(_cyan("🎯 ASSIST - Catalogue des catégories de mots-clés")))
    print(_bold(_cyan("=" * 70)))
    print()
    print(f"  {_dim('Utilisation :')}  {_yellow('python3 pwgen.py -i src.txt --cible-XXX [--cible-YYY ...]')}")
    print(f"  {_dim('Exemple    :')}  {_yellow('python3 pwgen.py -i src.txt --cible-rh --cible-it --stdout')}")
    print()
    print(f"  {_dim('Les mots-clés des cibles activées sont AJOUTÉS au source')}")
    print(f"  {_dim('(dédup auto) puis passent par toutes les règles.')}")
    print(f"  {_dim('Les sub-cibles (en italique) sont auto-incluses par les main.')}")
    print()

    for cat in ASSIST_CATEGORIES:
        is_main = cat.get("is_main", False)
        # En-tête : [TAG] --cible-id  label
        tag_str = ""
        if cat["tag"]:
            tag_str = _red(f"[{cat['tag']}] ") + " "
        if is_main:
            cible_str = _bold(_green(f"--cible-{cat['cible']}"))
        else:
            cible_str = _dim(_blue(f"(sub: {cat['cible']})"))
        label_str = _bold(cat["label"]) if is_main else _dim(cat["label"])
        print(f"  {tag_str}{cible_str}  {label_str}")
        # Ajoute la liste des includes pour les main
        if is_main and cat.get("includes"):
            inc_list = ", ".join(_cyan(i) for i in cat["includes"])
            print(f"      {_dim('→ auto-inclut:')} {inc_list}")

        # Contexte
        if cat.get("context"):
            print(f"      {_dim(cat['context'])}")

        # Mots-clés sur une ligne séparée pour lisibilité
        kws = [k for k in cat["keywords"] if not k.startswith("#")]
        commented = [k for k in cat["keywords"] if k.startswith("#")]
        if kws:
            kw_line = ", ".join(_yellow(k) for k in kws)
            print(f"      ➜  {kw_line}")
        for c in commented:
            print(f"      {_dim(c)}")
        print()

    # Récap final
    total_kw = sum(
        len([k for k in c["keywords"] if not k.startswith("#")])
        for c in ASSIST_CATEGORIES
    )
    cibles = list_cibles()
    print(_bold(_cyan("=" * 70)))
    print(_bold(f"  📋 {len(ASSIST_CATEGORIES)} catégories, {total_kw} mots-clés au total"))
    print()
    main_cibles = [c["cible"] for c in ASSIST_CATEGORIES if c.get("is_main")]
    sub_cibles = [c["cible"] for c in ASSIST_CATEGORIES if not c.get("is_main")]
    print(f"  {_dim('Flags main disponibles :')}")
    print(f"  {_yellow(', '.join('--cible-' + c for c in main_cibles))}")
    print()
    print(f"  {_dim('Sub-cibles (auto-incluses) :')} {_blue(', '.join(sub_cibles))}")
    print()
    print(_dim("  ⚡ Combine plusieurs flags : --cible-rh --cible-it"))
    print(_dim("  ⚡ Édite core/assist.py pour ajouter tes propres catégories"))
    print()
    return 0

"""
Mode --assist : questionnaire interactif pour suggérer des mots-clés à ajouter
manuellement au fichier source.

PRINCIPE : aucune écriture fichier, aucune génération. Le script pose des
questions oui/non sur la cible, et pour chaque réponse positive affiche un
ensemble de mots-clés contextuels (acronymes métier, abréviations, termes
courants) que l'utilisateur peut copier-coller dans son fichier source.

ÉDITION : ajoute tes propres questions dans ASSIST_QUESTIONS ci-dessous.
Le format est volontairement simple :

    {
        "q":        question (chaîne, finit par ' ?')
        "context":  explication courte sur pourquoi ces mots-clés
        "keywords": liste de chaînes (les mots à suggérer)
    }
"""

from typing import List, Dict, Any


# ============================================================================
# DONNÉES ÉDITABLES : ajoute / modifie les entrées ci-dessous selon ton besoin
# ============================================================================
ASSIST_QUESTIONS: List[Dict[str, Any]] = [
    {
        "q": "La cible est-elle un organisme de formation (CFA, école pro, "
             "centre de ressources) ?",
        "context": "Les organismes de formation utilisent des acronymes métier "
                   "très spécifiques (CDR = Centre De Ressources, OPCO, CPF, "
                   "AFPA…). Souvent intégrés tels quels dans les MDP.",
        "keywords": [
            "cdr", "cfa", "afpa", "opco", "cpf", "formation", "stagiaire",
            "session", "module", "epcc", "afdas",
        ],
    },
    {
        "q": "La cible est-elle une mairie / collectivité territoriale "
             "(commune, EPCI, syndicat) ?",
        "context": "Acronymes administration FR. Le nom de la ville + code "
                   "département + 'mairie' sont des combinaisons classiques.",
        "keywords": [
            "mairie", "ville", "conseil", "epci", "syndicat", "commune",
            "communaute", "agglomeration",
        ],
    },
    {
        "q": "La cible est-elle une PME / société commerciale (SARL, SAS, "
             "groupe) ?",
        "context": "Forme juridique, raison sociale, abréviation. Souvent "
                   "concaténé avec le nom du dirigeant ou de la ville.",
        "keywords": [
            "sarl", "sas", "sa", "eurl", "scic", "groupe", "holding",
            "societe", "entreprise",
        ],
    },
    {
        "q": "La cible est-elle dans le médical (cabinet, clinique, hôpital, "
             "EHPAD, libéral) ?",
        "context": "Vocabulaire santé FR. Les EHPAD/cliniques privées ont "
                   "souvent des MDP très basiques (cabinet+année, dr+nom…).",
        "keywords": [
            "cabinet", "clinique", "hopital", "ehpad", "medecin", "infirmier",
            "infirmiere", "secretaire", "dr", "kine", "podo",
        ],
    },
    {
        "q": "La cible est-elle une école / établissement scolaire (primaire, "
             "collège, lycée, faculté) ?",
        "context": "Nom d'établissement, acronymes éducation nationale, "
                   "rentrée, classes…",
        "keywords": [
            "ecole", "college", "lycee", "fac", "universite", "rectorat",
            "academie", "rentree", "eleve", "prof",
        ],
    },
    {
        "q": "La cible est-elle une association / club / asso 1901 ?",
        "context": "Format 'asso + nom' ou 'club + thème' très répandus, "
                   "abréviations courtes.",
        "keywords": [
            "asso", "association", "club", "amicale", "comite", "union",
            "federation",
        ],
    },
    {
        "q": "Veux-tu inclure les MDP IT/sysadmin classiques (cibles "
             "techniques: serveur, switch, AD) ?",
        "context": "Vocabulaire admin systèmes universel. Toujours pertinent "
                   "même pour cibles non-IT (ergonomie de saisie).",
        "keywords": [
            "root", "admin", "administrator", "user", "service", "prod",
            "dev", "test", "preprod", "config", "default", "guest",
        ],
    },
    {
        "q": "Veux-tu inclure les mots-clés 'personnels' (cibles individuelles "
             ": prénoms, animaux, voiture) ?",
        "context": "Termes courants pour MDP perso (animal de compagnie, "
                   "marque préférée, hobby). Pense à ajouter le prénom réel "
                   "de la cible si connu.",
        "keywords": [
            "moi", "amour", "chat", "chien", "papa", "maman", "famille",
            "bisous", "soleil", "etoile",
        ],
    },
    {
        "q": "La cible utilise-t-elle un nom commercial / marque de produit "
             "dans son organisation ?",
        "context": "Le nom du produit phare, l'abréviation interne, le projet "
                   "principal sont régulièrement réutilisés en MDP.",
        "keywords": [
            "# Ajoute ici le nom du produit/marque/projet observé",
        ],
    },
    {
        "q": "Inclure les mots-clés affectifs FR (cibles individuelles : pet "
             "names, mots tendres) ?",
        "context": "Statistiques Projet Richelieu / NordPass : 'doudou', "
                   "'loulou', 'chouchou' sont dans le top 14 des MDP FR. "
                   "'soleil', 'cheval', 'jetaime' aussi très fréquents.",
        "keywords": [
            "doudou", "loulou", "chouchou", "mamour", "bisous", "amour",
            "jetaime", "bonjour", "soleil", "cheval", "princesse",
        ],
    },
    {
        "q": "Inclure les villes FR principales (cible résidant ou travaillant "
             "dans une grande ville) ?",
        "context": "'marseille' est #11 dans le top FR. Les habitants utilisent "
                   "très souvent le nom de leur ville comme base de MDP. Ajoute "
                   "manuellement la ville exacte si tu la connais.",
        "keywords": [
            "marseille", "paris", "lyon", "toulouse", "bordeaux", "nice",
            "lille", "nantes", "strasbourg", "rennes", "montpellier", "rouen",
        ],
    },
    {
        "q": "Inclure les prénoms FR très fréquents en MDP (cible individuelle "
             "ou prénom inconnu) ?",
        "context": "'nicolas' est dans le top 25 FR. Si tu connais le prénom "
                   "exact de la cible, ajoute-le manuellement. Sinon, ces "
                   "prénoms statistiquement fréquents couvrent une partie.",
        "keywords": [
            "nicolas", "julien", "thomas", "camille", "martin", "dupont",
            "lucas", "hugo", "leo", "alex", "louis", "gabriel",
        ],
    },

    # ========================================================================
    # PENTEST ENTREPRISE - patterns observés en mission red team / spray AD
    # ========================================================================
    {
        "q": "[PENTEST] Cibler le helpdesk / MDP de réinitialisation "
             "(comptes fraîchement créés, post-reset) ?",
        "context": "Les MDP par défaut de helpdesk/IT sont une mine d'or : "
                   "Welcome123, Changeme, Reset+année, Temp+année, Bienvenue. "
                   "Souvent non changés par les utilisateurs.",
        "keywords": [
            "welcome", "Welcome", "changeme", "Changeme", "reset", "Reset",
            "temp", "Temp", "bienvenue", "Bienvenue", "nouveau", "Nouveau",
            "initial",
        ],
    },
    {
        "q": "[PENTEST] Cibler des comptes de service AD (svc_xxx, sa_xxx, "
             "scheduled tasks) ?",
        "context": "Comptes de service rarement changés (jamais expirent), "
                   "souvent avec MDP basique car contraintes legacy. Bases "
                   "courantes pour spray.",
        "keywords": [
            "service", "svc", "sql", "backup", "monitor", "scheduler",
            "scheduled", "report", "exchange", "sharepoint", "iis", "apache",
            "tomcat", "jenkins",
        ],
    },
    {
        "q": "[PENTEST] Inclure les noms de départements / divisions FR ?",
        "context": "Beaucoup d'utilisateurs intègrent leur département dans "
                   "leur MDP (compta2025, rh!, achats…). Aussi utilisé pour "
                   "comptes génériques de service.",
        "keywords": [
            "compta", "comptable", "rh", "drh", "finance", "achats", "achat",
            "juridique", "marketing", "commercial", "vente", "production",
            "prod", "qualite", "hse", "logistique", "direction", "siege",
            "secretariat", "informatique", "it",
        ],
    },
    {
        "q": "[PENTEST] Inclure les mots-clés infra Microsoft (Windows/AD/"
             "Exchange/O365/SharePoint) ?",
        "context": "Stack Microsoft = 80% des SI entreprise FR. Les comptes "
                   "techniques utilisent souvent le nom du produit.",
        "keywords": [
            "windows", "Windows", "microsoft", "office", "office365", "o365",
            "exchange", "Exchange", "sharepoint", "outlook", "teams",
            "domain", "krbtgt", "kerberos", "ldap", "dc",
        ],
    },
    {
        "q": "[PENTEST] Inclure les mots-clés virtualisation / Cloud "
             "(VMware, Citrix, AWS, Azure, GCP) ?",
        "context": "Comptes admin de l'infra virtu / cloud. MDP souvent "
                   "partagés entre équipes IT, recyclés.",
        "keywords": [
            "vmware", "vcenter", "esxi", "vsphere", "citrix", "horizon",
            "hyperv", "aws", "azure", "gcp", "openstack", "kubernetes", "k8s",
            "docker", "nutanix",
        ],
    },
    {
        "q": "[PENTEST] Inclure les vendeurs d'équipements réseau / sécurité "
             "(Cisco, Fortinet, Palo, Sophos) ?",
        "context": "Comptes admin sur switches, firewalls, NAC. Identifiants "
                   "souvent par défaut ou avec marque dans le MDP.",
        "keywords": [
            "cisco", "Cisco", "fortinet", "fortigate", "fortiweb", "juniper",
            "palo", "paloalto", "sophos", "watchguard", "stormshield",
            "checkpoint", "fortimanager", "panorama",
        ],
    },
    {
        "q": "[PENTEST] La cible est-elle dans la banque / assurance / "
             "finance ?",
        "context": "Vocabulaire bancaire FR. Comptes back-office, conseillers, "
                   "gestionnaires utilisent souvent les termes métier.",
        "keywords": [
            "banque", "credit", "agios", "compte", "epargne", "credit",
            "assurance", "mutuelle", "courtier", "conseiller", "gestionnaire",
            "client", "iban", "bic", "ca", "bnp", "lcl", "sg",
        ],
    },
    {
        "q": "[PENTEST] La cible est-elle dans l'industrie / production "
             "(usine, manufacture, ICS/SCADA) ?",
        "context": "Atelier, OT, qualité, sécurité industrielle. MDP souvent "
                   "fixés par contraintes équipement (8 char max, pas de "
                   "spéciaux). Recyclés entre stations.",
        "keywords": [
            "usine", "atelier", "production", "qualite", "securite", "hse",
            "sst", "iso9001", "supervision", "scada", "ihm", "automate",
            "operateur", "chef",
        ],
    },
    {
        "q": "[PENTEST] La cible est-elle dans le retail / grande distribution "
             "(magasin, caisse, stock) ?",
        "context": "Comptes caissier, gestionnaire de rayon, dépôt. MDP "
                   "souvent identiques entre magasins de la même enseigne.",
        "keywords": [
            "magasin", "caisse", "rayon", "stock", "depot", "vendeur",
            "vendeuse", "manager", "directeur", "siege", "franchise",
        ],
    },
    {
        "q": "[PENTEST] Inclure les saisons FR (politique de rotation MDP "
             "trimestrielle / annuelle) ?",
        "context": "Politiques RH 'changement tous les 90 jours' → MDP basés "
                   "sur la saison courante + année. Top pattern enterprise FR.",
        "keywords": [
            "ete", "Ete", "hiver", "Hiver", "printemps", "Printemps",
            "automne", "Automne", "summer", "Summer", "winter", "Winter",
            "spring", "Spring", "autumn", "fall",
        ],
    },
    {
        "q": "[PENTEST] Inclure les mois FR (politique mensuelle ou MDP "
             "'mois année') ?",
        "context": "Pattern 'Janvier2025!' / 'Mars2024@' fréquent quand la "
                   "politique RH force changement mensuel.",
        "keywords": [
            "janvier", "fevrier", "mars", "avril", "mai", "juin", "juillet",
            "aout", "septembre", "octobre", "novembre", "decembre",
            "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin", "Juillet",
            "Aout", "Septembre", "Octobre", "Novembre", "Decembre",
        ],
    },
    # ====================================================================
    # AJOUTE TES QUESTIONS ICI (copie le format exact ci-dessus)
    # Exemple :
    # {
    #     "q": "La cible est-elle dans le BTP / construction ?",
    #     "context": "Acronymes BTP, marques d'outillage...",
    #     "keywords": ["btp", "chantier", "macon", "elec"],
    # },
    # ====================================================================
]


# ============================================================================
# LOGIQUE INTERACTIVE - en principe pas à modifier
# ============================================================================
def _prompt_yn(question: str, idx: int, total: int) -> str:
    """Lit une réponse o/n/q. Retourne 'o', 'n', ou 'q' (quit)."""
    try:
        raw = input(f"  [{idx}/{total}] {question} [o/n/q] ").strip().lower()
    except (EOFError, KeyboardInterrupt):
        return "q"
    if raw in ("o", "oui", "y", "yes"):
        return "o"
    if raw in ("q", "quit", "quitter", "exit"):
        return "q"
    return "n"


def run_assist() -> int:
    """
    Lance le questionnaire interactif. N'écrit RIEN, affiche seulement les
    mots-clés à ajouter manuellement.

    Returns:
        0 si terminé normalement, 1 si interrompu.
    """
    print()
    print("=" * 70)
    print("🎯 MODE --assist : suggestions de mots-clés pour ta wordlist")
    print("=" * 70)
    print()
    print("Je vais te poser des questions sur la cible. Pour chaque 'oui',")
    print("je t'affiche les mots-clés contextuels à AJOUTER manuellement")
    print("dans ton fichier source.txt. Aucun fichier n'est créé.")
    print()
    print("Réponds : [o]ui / [n]on / [q]uitter")
    print()

    collected: List[str] = []
    total = len(ASSIST_QUESTIONS)

    for i, item in enumerate(ASSIST_QUESTIONS, 1):
        ans = _prompt_yn(item["q"], i, total)
        if ans == "q":
            print("\n⛔ Interrompu.")
            break
        if ans != "o":
            continue

        print()
        print(f"     💡 {item['context']}")
        print(f"     ➜ Mots-clés suggérés :")
        for kw in item["keywords"]:
            print(f"        {kw}")
        print()
        collected.extend(item["keywords"])

    # Récap : dédup en gardant l'ordre
    seen = set()
    unique = []
    for kw in collected:
        if kw not in seen:
            seen.add(kw)
            unique.append(kw)

    if not unique:
        print()
        print("Aucun mot-clé collecté. Édite core/assist.py pour ajouter des")
        print("questions adaptées à ton contexte.")
        return 0

    print()
    print("=" * 70)
    print(f"📋 RÉCAP : {len(unique)} mots-clés uniques à AJOUTER dans ton source")
    print("=" * 70)
    print()
    print("  Copie-colle dans source.txt (un mot par ligne) :")
    print()
    for kw in unique:
        print(f"    {kw}")
    print()
    print("  Ou en une ligne shell pour pipe rapide :")
    print(f"    printf '%s\\n' {' '.join(repr(k) for k in unique)} >> source.txt")
    print()
    print("  Puis génère :")
    print("    python3 pwgen.py -i source.txt --stdout")
    print()
    print("💡 N'oublie pas d'ajouter les éléments SPÉCIFIQUES à ta cible :")
    print("   - Nom/prénom de la personne ou du dirigeant")
    print("   - Nom de l'entreprise + abréviation")
    print("   - Ville + code postal + département")
    print("   - Année de création / d'événement clé")
    print()
    return 0

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

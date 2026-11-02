"""Étape 1 : structures de données et structures de contrôle.

Une fiche de livre est un tuple ``(titre, auteur, annee)``.

Dans cette étape, écrivez des boucles ``for`` classiques : les compréhensions
arrivent à l'étape 2.
"""

Fiche = tuple[str, str, int]


def lire_fiche(ligne: str) -> Fiche:
    """Transforme ``"Titre ; Auteur ; 1954"`` en fiche ``(titre, auteur, annee)``.

    Les espaces autour de chaque champ sont supprimés et l'année est convertie
    en entier. Lève ``ValueError`` si la ligne n'a pas exactement trois champs,
    ou si l'année n'est pas un entier.
    """
    champs = ligne.split(";")
    if len(champs) != 3:
        raise ValueError(f"3 champs attendus, {len(champs)} trouvés : {ligne!r}")
    titre, auteur, annee = (champ.strip() for champ in champs)
    return titre, auteur, int(annee)


def periode(annee: int) -> str:
    """Classe une année : ``"classique"`` avant 1900, ``"moderne"`` de 1900 à
    1999, ``"contemporain"`` à partir de 2000."""
    if annee < 1900:
        return "classique"
    elif annee < 2000:
        return "moderne"
    else:
        return "contemporain"


def auteurs(fiches: list[Fiche]) -> set[str]:
    """Renvoie l'ensemble des auteurs, sans doublon."""
    resultat: set[str] = set()
    for _, auteur, _ in fiches:
        resultat.add(auteur)
    return resultat


def index_par_titre(fiches: list[Fiche]) -> dict[str, Fiche]:
    """Renvoie un dictionnaire titre -> fiche. En cas de titres identiques, la
    dernière fiche l'emporte."""
    index: dict[str, Fiche] = {}
    for fiche in fiches:
        index[fiche[0]] = fiche
    return index


def compter_par_auteur(fiches: list[Fiche]) -> dict[str, int]:
    """Renvoie le nombre de livres de chaque auteur."""
    compte: dict[str, int] = {}
    for _, auteur, _ in fiches:
        compte[auteur] = compte.get(auteur, 0) + 1
    return compte


def premier_de(fiches: list[Fiche], auteur: str) -> Fiche | None:
    """Renvoie la première fiche de ``auteur`` dans l'ordre de la liste, ou
    ``None`` s'il n'y en a aucune."""
    for fiche in fiches:
        if fiche[1] == auteur:
            return fiche
    return None


def auteur_le_plus_present(fiches: list[Fiche]) -> str | None:
    """Renvoie l'auteur qui a le plus de livres, ou ``None`` si la liste est
    vide. En cas d'égalité, l'auteur rencontré le premier l'emporte."""
    meilleur: str | None = None
    meilleur_nombre = 0
    for auteur, nombre in compter_par_auteur(fiches).items():
        if nombre > meilleur_nombre:
            meilleur, meilleur_nombre = auteur, nombre
    return meilleur

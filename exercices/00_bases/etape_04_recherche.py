"""Étape 4 : fonctions, valeurs par défaut, ``*args`` et ``**kwargs``."""

Fiche = tuple[str, str, int]

#: Position de chaque champ dans une fiche. Constante en lecture seule.
CHAMPS = {"titre": 0, "auteur": 1, "annee": 2}


def rechercher(fiches: list[Fiche], **criteres: str | int) -> list[Fiche]:
    """Renvoie les fiches qui satisfont **tous** les critères.

    Les critères possibles sont ``titre``, ``auteur`` et ``annee``. Sans
    critère, toutes les fiches sont renvoyées. Un critère inconnu lève
    ``ValueError`` avec son nom dans le message.

    >>> rechercher(fiches, auteur="Victor Hugo", annee=1862)
    """
    for nom in criteres:
        if nom not in CHAMPS:
            raise ValueError(f"critère inconnu : {nom}")
    resultat = []
    for fiche in fiches:
        if all(fiche[CHAMPS[nom]] == valeur for nom, valeur in criteres.items()):
            resultat.append(fiche)
    return resultat


def moyenne_annees(*annees: int, arrondi: int = 1) -> float:
    """Renvoie la moyenne des années, arrondie à ``arrondi`` décimales.

    Lève ``ValueError`` si aucune année n'est fournie.
    """
    if not annees:
        raise ValueError("il faut au moins une année")
    return round(sum(annees) / len(annees), arrondi)


def formater(fiche: Fiche, gabarit: str = "{titre} ({auteur}, {annee})") -> str:
    """Met en forme une fiche selon ``gabarit``, qui peut utiliser les champs
    ``{titre}``, ``{auteur}`` et ``{annee}``."""
    titre, auteur, annee = fiche
    return gabarit.format(titre=titre, auteur=auteur, annee=annee)


def fusionner(*catalogues: list[Fiche]) -> list[Fiche]:
    """Fusionne plusieurs catalogues en un seul, sans doublon.

    L'ordre est celui de la première apparition de chaque fiche. Aucun
    catalogue n'est modifié.
    """
    deja_vues = set()
    resultat = []
    for catalogue in catalogues:
        for fiche in catalogue:
            if fiche not in deja_vues:
                deja_vues.add(fiche)
                resultat.append(fiche)
    return resultat

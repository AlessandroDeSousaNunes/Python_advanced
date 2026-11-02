"""Étape 2 : compréhensions de liste, de dictionnaire et d'ensemble.

Chaque fonction tient en une seule expression ``return``, sans boucle ``for``
classique (les tests le vérifient).
"""

Fiche = tuple[str, str, int]


def titres(fiches: list[Fiche]) -> list[str]:
    """Renvoie les titres, dans l'ordre des fiches."""
    return [titre for titre, _, _ in fiches]


def parus_entre(fiches: list[Fiche], debut: int, fin: int) -> list[Fiche]:
    """Renvoie les fiches parues entre ``debut`` et ``fin``, bornes comprises,
    dans l'ordre d'origine."""
    return [fiche for fiche in fiches if debut <= fiche[2] <= fin]


def longueurs_titres(fiches: list[Fiche]) -> dict[str, int]:
    """Renvoie un dictionnaire titre -> nombre de caractères du titre."""
    return {titre: len(titre) for titre, _, _ in fiches}


def initiales_auteurs(fiches: list[Fiche]) -> set[str]:
    """Renvoie l'ensemble des initiales (en majuscule) des noms d'auteurs."""
    return {auteur[0].upper() for _, auteur, _ in fiches if auteur}


def titres_par_auteur(fiches: list[Fiche]) -> dict[str, list[str]]:
    """Renvoie un dictionnaire auteur -> liste de ses titres, dans l'ordre des
    fiches."""
    return {
        auteur: [titre for titre, a, _ in fiches if a == auteur]
        for _, auteur, _ in fiches
    }


def annees_distinctes(fiches: list[Fiche]) -> list[int]:
    """Renvoie les années de parution sans doublon, triées par ordre croissant."""
    return sorted({annee for _, _, annee in fiches})

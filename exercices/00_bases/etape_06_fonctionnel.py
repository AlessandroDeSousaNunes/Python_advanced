"""Étape 6 : programmation fonctionnelle sur les livres de l'étape 5.

Toutes les fonctions sont pures : elles ne modifient ni la liste reçue, ni les
livres qu'elle contient.

Cette étape utilise la classe ``Livre`` de l'étape 5 : terminez-la d'abord.
"""

from collections.abc import Callable
from functools import reduce
from itertools import groupby

from etape_05_bibliotheque import Livre

#: Un filtre reçoit un livre et dit s'il le garde.
Filtre = Callable[[Livre], bool]


def titres_tries(livres: list[Livre]) -> list[str]:
    """Renvoie les titres triés par ordre alphabétique, sans tenir compte des
    majuscules."""
    return sorted((livre.titre for livre in livres), key=str.lower)


def par_auteur(livres: list[Livre]) -> dict[str, list[Livre]]:
    """Regroupe les livres par auteur. Les auteurs apparaissent dans l'ordre de
    leur premier livre, et les livres dans l'ordre de la liste."""
    groupes: dict[str, list[Livre]] = {}
    for livre in livres:
        groupes.setdefault(livre.auteur, []).append(livre)
    return groupes


def par_auteur_tries(livres: list[Livre]) -> dict[str, list[Livre]]:
    """Même regroupement que ``par_auteur``, mais les auteurs sont dans l'ordre
    alphabétique. À écrire avec ``sorted`` et ``itertools.groupby``."""
    tries = sorted(livres, key=lambda livre: livre.auteur)
    return {
        auteur: list(groupe)
        for auteur, groupe in groupby(tries, key=lambda livre: livre.auteur)
    }


def publie_apres(annee: int) -> Filtre:
    """Renvoie un filtre qui accepte les livres parus strictement après
    ``annee``."""
    return lambda livre: livre.annee > annee


def ecrit_par(auteur: str) -> Filtre:
    """Renvoie un filtre qui accepte les livres de ``auteur``."""
    return lambda livre: livre.auteur == auteur


def appliquer_filtres(livres: list[Livre], *filtres: Filtre) -> list[Livre]:
    """Renvoie les livres acceptés par **tous** les filtres, dans l'ordre
    d'origine. Sans filtre, renvoie une copie de la liste."""
    return [livre for livre in livres if all(f(livre) for f in filtres)]


def normaliser_auteurs(livres: list[Livre]) -> list[Livre]:
    """Renvoie de **nouveaux** livres dont l'auteur est nettoyé : espaces
    retirés aux extrémités et majuscule à chaque mot (``"  victor HUGO "`` donne
    ``"Victor Hugo"``). Les livres d'origine ne sont pas modifiés."""
    return [
        Livre(livre.titre, livre.auteur.strip().title(), livre.annee)
        for livre in livres
    ]


def total_mots_titres(livres: list[Livre]) -> int:
    """Renvoie le nombre total de mots dans les titres, calculé avec
    ``functools.reduce``."""
    return reduce(lambda total, livre: total + len(livre.titre.split()), livres, 0)


def enchainer(
    livres: list[Livre], *etapes: Callable[[list[Livre]], list[Livre]]
) -> list[Livre]:
    """Applique les étapes à ``livres`` l'une après l'autre, de gauche à
    droite : ``enchainer(livres, f, g)`` vaut ``g(f(livres))``."""
    for etape in etapes:
        livres = etape(livres)
    return livres

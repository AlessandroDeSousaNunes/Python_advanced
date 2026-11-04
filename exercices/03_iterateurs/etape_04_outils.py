"""Étape 4 : expressions génératrices, ``itertools`` et ``functools``.

Chaque fonction tient en quelques lignes si l'on choisit le bon outil de la
bibliothèque standard. Les imports utiles sont déjà là.
"""

import operator
from collections import deque
from collections.abc import Iterable, Iterator
from functools import lru_cache, reduce
from itertools import (
    combinations,
    count,
    groupby,
    islice,
    takewhile,
)


def somme_des_carres(n: int) -> int:
    """Renvoie ``0² + 1² + … + (n - 1)²``, avec une expression génératrice."""
    return sum(i * i for i in range(n))


def premiers() -> Iterator[int]:
    """Produit les nombres premiers sans fin : 2, 3, 5, 7, 11…"""
    trouves: list[int] = []
    for n in count(2):
        # n est premier si aucun premier déjà trouvé (jusqu'à sa racine) ne le divise.
        if all(n % p != 0 for p in takewhile(lambda p: p * p <= n, trouves)):
            trouves.append(n)
            yield n


def n_premiers(n: int) -> list[int]:
    """Renvoie les ``n`` premiers nombres premiers."""
    return list(islice(premiers(), n))


def jusqu_a(flux: Iterable[int], limite: int) -> Iterator[int]:
    """Produit les éléments de ``flux`` tant qu'ils sont strictement inférieurs
    à ``limite``, puis s'arrête au premier qui ne l'est pas."""
    return takewhile(lambda x: x < limite, flux)


def fenetres[T](iterable: Iterable[T], taille: int) -> Iterator[tuple[T, ...]]:
    """Produit les fenêtres glissantes de ``taille`` éléments consécutifs :
    ``fenetres("abcd", 2)`` produit ``('a', 'b') ('b', 'c') ('c', 'd')``.
    Paresseux. Lève ``ValueError`` dès l'appel si ``taille < 1``."""
    if taille < 1:
        raise ValueError("la taille doit valoir au moins 1")
    return _fenetres(iterable, taille)


def _fenetres[T](iterable: Iterable[T], taille: int) -> Iterator[tuple[T, ...]]:
    # Une deque avec maxlen oublie toute seule le plus ancien élément.
    fenetre: deque[T] = deque(maxlen=taille)
    for element in iterable:
        fenetre.append(element)
        if len(fenetre) == taille:
            yield tuple(fenetre)


def encoder_rle(texte: str) -> list[tuple[str, int]]:
    """Codage par plages : ``"aaabcc"`` donne ``[("a", 3), ("b", 1), ("c", 2)]``."""
    return [(lettre, len(list(groupe))) for lettre, groupe in groupby(texte)]


def decoder_rle(plages: Iterable[tuple[str, int]]) -> str:
    """Inverse de ``encoder_rle``."""
    return "".join(lettre * nombre for lettre, nombre in plages)


def poignees_de_main(personnes: Iterable[str]) -> list[tuple[str, str]]:
    """Toutes les paires de personnes distinctes, chaque paire une seule fois,
    dans l'ordre de ``personnes``."""
    return list(combinations(personnes, 2))


def produit(nombres: Iterable[float]) -> float:
    """Produit des nombres, avec ``functools.reduce`` (1 pour un itérable vide)."""
    return reduce(operator.mul, nombres, 1)


@lru_cache(maxsize=None)
def nombre_de_chemins(lignes: int, colonnes: int) -> int:
    """Nombre de chemins du coin haut gauche au coin bas droit d'une grille de
    ``lignes`` × ``colonnes`` cases, en n'allant que vers la droite ou vers le
    bas. Récursif, mémoïsé avec ``functools.lru_cache``."""
    if lignes == 1 or colonnes == 1:
        return 1
    return nombre_de_chemins(lignes - 1, colonnes) + nombre_de_chemins(
        lignes, colonnes - 1
    )

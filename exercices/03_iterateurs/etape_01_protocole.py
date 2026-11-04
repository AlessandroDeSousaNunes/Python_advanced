"""Étape 1 : le protocole d'itération.

Un itérable fournit ``__iter__``, qui renvoie un itérateur. Un itérateur
fournit ``__next__``, qui renvoie l'élément suivant ou lève ``StopIteration``.
``for`` n'est qu'une boucle ``while`` autour de ``iter`` et ``next``.
"""

from collections.abc import Iterable, Iterator
from typing import Self


def parcourir[T](iterable: Iterable[T]) -> list[T]:
    """Renvoie la liste des éléments de ``iterable``, **sans** boucle ``for``
    ni compréhension ni ``list(...)`` : uniquement ``iter``, ``next`` et
    ``StopIteration``, comme le fait un ``for`` en coulisses."""
    iterateur = iter(iterable)
    resultat: list[T] = []
    while True:
        try:
            element = next(iterateur)
        except StopIteration:
            return resultat
        resultat.append(element)


def premier[T](iterable: Iterable[T], defaut: T | None = None) -> T | None:
    """Renvoie le premier élément de ``iterable``, ou ``defaut`` s'il est vide."""
    return next(iter(iterable), defaut)


def prendre[T](iterateur: Iterator[T], n: int) -> list[T]:
    """Consomme **exactement** ``n`` éléments de ``iterateur`` (moins s'il
    s'épuise avant) et les renvoie. Le reste de l'itérateur reste disponible."""
    resultat: list[T] = []
    for _ in range(n):
        try:
            resultat.append(next(iterateur))
        except StopIteration:
            break
    return resultat


def est_iterable(obj: object) -> bool:
    """Vrai si ``iter(obj)`` réussit."""
    try:
        iter(obj)  # type: ignore[call-overload]
    except TypeError:
        return False
    return True


def est_iterateur(obj: object) -> bool:
    """Vrai si ``obj`` est un itérateur : il a une méthode ``__next__`` et
    ``iter(obj)`` le renvoie lui-même."""
    return hasattr(obj, "__next__") and est_iterable(obj) and iter(obj) is obj  # type: ignore[call-overload]


class CompteARebours:
    """Itérateur qui produit ``debut``, ``debut - pas``, ``debut - 2 * pas``…
    tant que la valeur est strictement positive.

    Lève ``ValueError`` si ``pas`` n'est pas strictement positif.
    """

    def __init__(self, debut: int, pas: int = 1) -> None:
        if pas <= 0:
            raise ValueError("le pas doit être strictement positif")
        self.courant = debut
        self.pas = pas

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> int:
        if self.courant <= 0:
            raise StopIteration
        valeur = self.courant
        self.courant -= self.pas
        return valeur

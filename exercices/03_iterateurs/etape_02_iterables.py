"""Étape 2 : séparer l'itérable de l'itérateur.

Un itérateur s'épuise après un passage. Un itérable **réitérable** fabrique un
itérateur neuf à chaque appel de ``__iter__`` : chaque ``for`` repart du début.
"""

from collections.abc import Iterable, Iterator
from typing import Self


class IterIntervalle:
    """Itérateur sur les entiers de ``debut`` (inclus) à ``fin`` (exclue),
    de ``pas`` en ``pas``. Il s'épuise après un passage."""

    def __init__(self, debut: int, fin: int, pas: int) -> None:
        self.courant = debut
        self.fin = fin
        self.pas = pas

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> int:
        if self.courant >= self.fin:
            raise StopIteration
        valeur = self.courant
        self.courant += self.pas
        return valeur


class Intervalle:
    """Itérable **réitérable** : chaque parcours repart de ``debut``.

    Lève ``ValueError`` si ``pas`` n'est pas strictement positif.
    """

    def __init__(self, debut: int, fin: int, pas: int = 1) -> None:
        if pas <= 0:
            raise ValueError("le pas doit être strictement positif")
        self.debut = debut
        self.fin = fin
        self.pas = pas

    def __iter__(self) -> IterIntervalle:
        return IterIntervalle(self.debut, self.fin, self.pas)

    def __len__(self) -> int:
        """Nombre de valeurs produites, calculé sans les parcourir."""
        if self.fin <= self.debut:
            return 0
        # Division arrondie au-dessus : (fin - debut) / pas.
        return (self.fin - self.debut + self.pas - 1) // self.pas


class Playlist:
    """Une liste de titres, réitérable, construite à partir de n'importe quel
    itérable (y compris un générateur)."""

    def __init__(self, titres: Iterable[str]) -> None:
        self._titres = list(titres)

    def ajouter(self, titre: str) -> None:
        self._titres.append(titre)

    def __iter__(self) -> Iterator[str]:
        return iter(self._titres)

    def __len__(self) -> int:
        return len(self._titres)


def statistiques_erronee(valeurs: Iterable[float]) -> tuple[float, float, float]:
    """Version piégée, fournie : elle parcourt ``valeurs`` trois fois."""
    return min(valeurs), max(valeurs), sum(valeurs) / len(list(valeurs))


def statistiques(valeurs: Iterable[float]) -> tuple[float, float, float]:
    """Renvoie ``(minimum, maximum, moyenne)`` de ``valeurs``, qui peut être
    un générateur. Lève ``ValueError`` si ``valeurs`` est vide."""
    # Un seul parcours : un générateur ne peut être lu qu'une fois.
    minimum = maximum = 0.0
    total = 0.0
    nombre = 0
    for valeur in valeurs:
        if nombre == 0:
            minimum = maximum = valeur
        else:
            minimum = min(minimum, valeur)
            maximum = max(maximum, valeur)
        total += valeur
        nombre += 1
    if nombre == 0:
        raise ValueError("aucune valeur")
    return minimum, maximum, total / nombre

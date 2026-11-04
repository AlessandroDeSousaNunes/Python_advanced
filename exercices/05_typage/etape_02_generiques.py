"""Étape 2 : types génériques.

Une pile typée, puis des fonctions génériques : un paramètre de type libre,
contraint, ou borné.

Dans ce chapitre, les annotations font partie de ce que vous écrivez : les
tests lancent mypy sur ce fichier, et sur de petits programmes qui l'utilisent.
Les docstrings disent ce que mypy doit accepter ou refuser.
"""

from collections.abc import Callable, Iterable, Iterator, Sized


class PileVide(IndexError):
    """Levée par ``depiler`` et ``sommet`` sur une pile vide."""


class Pile[T]:
    """Une pile d'éléments de type ``T``.

    ``Pile[int]()`` refuse ``empiler("a")``, et ``depiler()`` y renvoie un
    ``int``. ``Pile(["a", "b"])`` est une ``Pile[str]``.
    """

    def __init__(self, elements: Iterable[T] = ()) -> None:
        """Les ``elements`` (n'importe quel itérable) sont empilés dans
        l'ordre : le dernier est au sommet. La pile garde sa propre liste."""
        self._elements: list[T] = list(elements)

    def empiler(self, element: T) -> None:
        self._elements.append(element)

    def depiler(self) -> T:
        """Retire et renvoie le sommet ; ``PileVide`` si la pile est vide."""
        if not self._elements:
            raise PileVide("pile vide")
        return self._elements.pop()

    def sommet(self) -> T:
        """Renvoie le sommet sans le retirer ; ``PileVide`` si la pile est vide."""
        if not self._elements:
            raise PileVide("pile vide")
        return self._elements[-1]

    def __len__(self) -> int:
        return len(self._elements)

    def __iter__(self) -> Iterator[T]:
        """Du sommet vers le fond, sans modifier la pile."""
        return reversed(self._elements)

    def __repr__(self) -> str:
        """``Pile([1, 2, 3])``, du fond vers le sommet."""
        return f"Pile({self._elements!r})"


def premier[T](elements: Iterable[T]) -> T | None:
    """Le premier élément de n'importe quel itérable (même infini), ou
    ``None`` s'il est vide. ``premier(["a"])`` est un ``str | None``."""
    return next(iter(elements), None)


def combiner[T: (int, str)](a: T, b: T) -> T:
    """``a + b`` : une somme pour deux entiers, une concaténation pour deux
    chaînes. Les deux arguments sont du même type, et le résultat aussi.
    ``combiner(1, "a")`` et ``combiner(1.5, 2.5)`` sont refusés."""
    return a + b


def plus_long[S: Sized](a: S, b: S) -> S:
    """Le plus long des deux (``a`` en cas d'égalité), du même type que les
    arguments. ``plus_long(1, 2)`` est refusé : un entier n'a pas de longueur."""
    return b if len(b) > len(a) else a


def inverser[A, B](paire: tuple[A, B]) -> tuple[B, A]:
    """``(1, "a")`` devient ``("a", 1)`` : un ``tuple[str, int]``."""
    premier_element, second_element = paire
    return second_element, premier_element


def regrouper[T, K](elements: Iterable[T], cle: Callable[[T], K]) -> dict[K, list[T]]:
    """Range les éléments par ``cle(element)``, dans l'ordre d'apparition.
    ``regrouper(["ab", "c"], len)`` est un ``dict[int, list[str]]``."""
    groupes: dict[K, list[T]] = {}
    for element in elements:
        groupes.setdefault(cle(element), []).append(element)
    return groupes

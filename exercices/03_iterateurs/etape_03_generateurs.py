"""Étape 3 : générateurs et ``yield``.

Une fonction qui contient ``yield`` renvoie un générateur : un itérateur qui
calcule chaque valeur à la demande et garde son état entre deux ``next``.
"""

from collections.abc import Iterable, Iterator


def compte_a_rebours(n: int) -> Iterator[int]:
    """Produit ``n``, ``n - 1``… jusqu'à 1."""
    while n > 0:
        yield n
        n -= 1


def naturels(debut: int = 0, pas: int = 1) -> Iterator[int]:
    """Produit ``debut``, ``debut + pas``, ``debut + 2 * pas``… sans fin."""
    valeur = debut
    while True:
        yield valeur
        valeur += pas


def fibonacci() -> Iterator[int]:
    """Produit la suite de Fibonacci sans fin : 0, 1, 1, 2, 3, 5, 8…"""
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b


def aplatir(elements: Iterable[object]) -> Iterator[object]:
    """Produit les éléments de ``elements`` en aplatissant récursivement les
    listes et les tuples imbriqués. Les autres objets (chaînes comprises) sont
    produits tels quels."""
    for element in elements:
        if isinstance(element, (list, tuple)):
            yield from aplatir(element)
        else:
            yield element


def par_paquets[T](iterable: Iterable[T], taille: int) -> Iterator[list[T]]:
    """Découpe ``iterable`` en listes de ``taille`` éléments (la dernière peut
    être plus courte). Paresseux : fonctionne sur un flux infini.

    Lève ``ValueError`` **dès l'appel** si ``taille < 1``.
    """
    # La vérification est faite ici, hors du générateur : un générateur ne
    # commence à s'exécuter qu'au premier next, l'erreur arriverait trop tard.
    if taille < 1:
        raise ValueError("la taille doit valoir au moins 1")
    return _paquets(iterable, taille)


def _paquets[T](iterable: Iterable[T], taille: int) -> Iterator[list[T]]:
    paquet: list[T] = []
    for element in iterable:
        paquet.append(element)
        if len(paquet) == taille:
            yield paquet
            paquet = []
    if paquet:
        yield paquet


def alterner[T](*iterables: Iterable[T]) -> Iterator[T]:
    """Produit un élément de chaque itérable à tour de rôle. Un itérable épuisé
    est retiré du tour, les autres continuent :
    ``alterner("abc", "12")`` produit ``a 1 b 2 c``."""
    iterateurs = [iter(it) for it in iterables]
    while iterateurs:
        encore = []
        for iterateur in iterateurs:
            try:
                yield next(iterateur)
            except StopIteration:
                continue
            encore.append(iterateur)
        iterateurs = encore


class Pile[T]:
    """Pile dont le parcours va du sommet vers la base."""

    def __init__(self) -> None:
        self._elements: list[T] = []

    def empiler(self, element: T) -> None:
        self._elements.append(element)

    def depiler(self) -> T:
        if not self._elements:
            raise IndexError("pile vide")
        return self._elements.pop()

    def __len__(self) -> int:
        return len(self._elements)

    def __iter__(self) -> Iterator[T]:
        for i in range(len(self._elements) - 1, -1, -1):
            yield self._elements[i]

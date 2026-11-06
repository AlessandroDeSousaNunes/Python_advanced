"""Un flux avec regard en avant."""

from collections import deque
from collections.abc import Iterable


class Flux[T]:
    """Enveloppe un itérable : on peut regarder les éléments à venir sans les
    consommer. Le flux ne tire de la source que ce qui est nécessaire.

    Le parser s'en sert pour « jeter un œil » au token suivant avant de
    décider quoi faire (par exemple : y a-t-il un ``=`` après ce nom ?).
    Les éléments déjà lus mais pas encore consommés attendent dans le tampon.
    """

    def __init__(self, source: Iterable[T]) -> None:
        self._source = iter(source)
        self._tampon: deque[T] = deque()

    def regarde(self, decalage: int = 0) -> T | None:
        """L'élément à ``decalage`` places devant, ou ``None`` en fin de flux."""
        while len(self._tampon) <= decalage:
            try:
                self._tampon.append(next(self._source))
            except StopIteration:
                return None
        return self._tampon[decalage]

    def avance(self) -> T | None:
        """Consomme et renvoie l'élément courant (``None`` en fin de flux)."""
        if self.regarde() is None:
            return None
        return self._tampon.popleft()

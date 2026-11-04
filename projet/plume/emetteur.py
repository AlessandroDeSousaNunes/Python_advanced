"""L'émetteur : produit du code ligne par ligne, avec l'indentation."""

from collections.abc import Iterator
from contextlib import contextmanager

from plume.erreurs import Position


class Emetteur:
    """Accumule des lignes indentées. Note aussi, pour chaque ligne produite,
    la position du source Plume dont elle provient (voir ``depuis``)."""

    def __init__(self, indentation: str = "    ") -> None:
        self.indentation = indentation
        self.niveau = 0
        self._lignes: list[str] = []
        self.correspondances: dict[int, Position] = {}
        self._origine: Position | None = None

    def ligne(self, texte: str = "") -> None:
        """Ajoute une ligne au niveau courant (une ligne vide reste vide)."""
        self._lignes.append(self.indentation * self.niveau + texte if texte else "")
        if self._origine is not None:
            self.correspondances[len(self._lignes)] = self._origine

    @contextmanager
    def bloc(self, vide: str | None = "pass") -> Iterator[None]:
        """Indente pour la durée du ``with``. Si rien n'a été émis dedans et que
        ``vide`` n'est pas ``None``, émet ``vide`` (un bloc Python ne peut pas
        être vide)."""
        avant = len(self._lignes)
        self.niveau += 1
        try:
            yield
            if len(self._lignes) == avant and vide is not None:
                self.ligne(vide)
        finally:
            self.niveau -= 1

    @contextmanager
    def depuis(self, position: Position) -> Iterator[None]:
        """Les lignes émises dans le ``with`` proviennent de ``position``."""
        avant = self._origine
        self._origine = position
        try:
            yield
        finally:
            self._origine = avant

    def texte(self) -> str:
        return "\n".join(self._lignes) + "\n" if self._lignes else ""

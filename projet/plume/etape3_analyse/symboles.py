"""La table des symboles : une pile de portées.

Une portée, c'est un dictionnaire « nom -> ce qu'on sait du nom ». Entrer dans
un bloc ``{`` empile une portée vide ; en sortir ``}`` la retire, et les noms
déclarés dedans disparaissent. Pour trouver un nom, on cherche du bloc le
plus intérieur vers le niveau principal.

On n'y range que des NOMS (variable, fonction, nombre de paramètres), jamais
de valeurs : les valeurs n'existent qu'à l'exécution, dans Python.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum

from plume.erreurs import Position


class Genre(Enum):
    VARIABLE = "variable"
    PARAMETRE = "paramètre"
    FONCTION = "fonction"
    PREDEFINIE = "fonction prédéfinie"


@dataclass(frozen=True)
class Symbole:
    nom: str
    genre: Genre
    position: Position | None = None
    nb_parametres: int = 0
    fonction: str | None = None
    """La fonction où le symbole est déclaré (``None`` : niveau principal)."""

    @property
    def est_fonction(self) -> bool:
        return self.genre in (Genre.FONCTION, Genre.PREDEFINIE)


type Instantane = list[dict[str, Symbole]]


class TableSymboles:
    def __init__(self) -> None:
        self._portees: list[dict[str, Symbole]] = [{}]

    @property
    def profondeur(self) -> int:
        """Nombre de portées ouvertes, la globale comprise."""
        return len(self._portees)

    @contextmanager
    def portee(self) -> Iterator[None]:
        """Ouvre une portée pour la durée du ``with`` ; la referme même si une
        exception traverse le bloc."""
        # @contextmanager (chapitre 4) : le code avant ``yield`` s'exécute à
        # l'entrée du ``with``, celui du ``finally`` à la sortie, même en cas
        # d'erreur. La portée est donc toujours refermée.
        self._portees.append({})
        try:
            yield
        finally:
            self._portees.pop()

    def declarer(self, symbole: Symbole) -> None:
        self._portees[-1][symbole.nom] = symbole

    def chercher(self, nom: str) -> Symbole | None:
        """Cherche ``nom`` de la portée courante vers la globale."""
        for portee in reversed(self._portees):
            if nom in portee:
                return portee[nom]
        return None

    def instantane(self) -> Instantane:
        """Une copie de l'état, pour pouvoir annuler (le REPL s'en sert)."""
        return [dict(portee) for portee in self._portees]

    def restaurer(self, instantane: Instantane) -> None:
        self._portees = [dict(portee) for portee in instantane]

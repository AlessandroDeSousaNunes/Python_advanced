"""Étape 4 : le protocole context manager, en classes.

with Gestionnaire(...) as valeur:   # valeur = __enter__()
    ...                             # __exit__(type, exc, tb) en sortie
"""

import time
from collections.abc import Callable
from pathlib import Path
from types import TracebackType
from typing import IO, Any, Literal, Self


class Chrono:
    """Mesure la durée du bloc ``with`` avec ``time.perf_counter``.
    ``duree`` vaut ``None`` avant la première sortie."""

    def __init__(self) -> None:
        self.duree: float | None = None
        self._debut = 0.0

    def __enter__(self) -> Self:
        self._debut = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        self.duree = time.perf_counter() - self._debut
        return False  # False : on ne cache pas l'exception éventuelle


class Ignorer:
    """Avale les exceptions des types donnés (et de leurs sous-classes), et
    laisse passer les autres. ``exception`` garde la dernière avalée."""

    def __init__(self, *types: type[BaseException]) -> None:
        self.types = types
        self.exception: BaseException | None = None

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if exc is not None and isinstance(exc, self.types):
            self.exception = exc
            return True  # True : l'exception est avalée
        return False


class Transaction[V]:
    """Rend un dictionnaire transactionnel : si le bloc ``with`` lève une
    exception, le dictionnaire retrouve (sur place) son contenu d'entrée, et
    l'exception se propage. ``as`` donne le dictionnaire lui-même."""

    def __init__(self, donnees: dict[str, V]) -> None:
        self.donnees = donnees
        self.annulee = False
        self._copie: dict[str, V] = {}

    def __enter__(self) -> dict[str, V]:
        self._copie = dict(self.donnees)
        self.annulee = False
        return self.donnees

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        if exc is not None:
            # Sur place : on vide puis on remet, sans créer un nouveau dict.
            self.donnees.clear()
            self.donnees.update(self._copie)
            self.annulee = True
        return False


class FichierChronometre:
    """L'exercice du cours, version classe : ouvre un fichier, mesure la durée
    d'utilisation, le ferme dans tous les cas, journalise une erreur éventuelle
    puis la laisse se propager.

    Messages envoyés à ``journal``, dans cet ordre :

    - ``"Erreur pendant l'utilisation de <chemin> : <repr de l'exception>"``
      (seulement en cas d'erreur) ;
    - ``"<chemin> fermé après <durée avec 3 décimales> s"``.
    """

    def __init__(
        self,
        chemin: str | Path,
        mode: str = "r",
        *,
        journal: Callable[[str], None] = print,
    ) -> None:
        self.chemin = chemin
        self.mode = mode
        self.journal = journal
        self.duree: float | None = None
        self._debut = 0.0
        self._fichier: IO[Any] | None = None

    def __enter__(self) -> IO[Any]:
        # On ouvre d'abord : si l'ouverture échoue, il n'y a rien à chronométrer.
        self._fichier = open(self.chemin, self.mode, encoding="utf-8")  # noqa: SIM115
        self._debut = time.perf_counter()
        return self._fichier

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> Literal[False]:
        if self._fichier is not None:
            self._fichier.close()
        self.duree = time.perf_counter() - self._debut
        if exc is not None:
            self.journal(f"Erreur pendant l'utilisation de {self.chemin} : {exc!r}")
        self.journal(f"{self.chemin} fermé après {self.duree:.3f} s")
        return False

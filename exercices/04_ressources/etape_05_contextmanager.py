"""Étape 5 : ``@contextmanager``.

@contextmanager
def gestionnaire():
    ...            # = __enter__
    try:
        yield x    # le corps du with s'exécute ici ; x est lié à « as »
    finally:
        ...        # = __exit__
"""

import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import IO, Any


@dataclass
class Mesure:
    """Ce que ``chrono`` lie à ``as``. ``duree`` est remplie en sortie."""

    duree: float | None = None


@contextmanager
def chrono() -> Iterator[Mesure]:
    """Mesure la durée du bloc ``with`` (``time.perf_counter``), même si le
    bloc lève une exception, qui se propage."""
    mesure = Mesure()
    debut = time.perf_counter()
    try:
        yield mesure
    finally:
        mesure.duree = time.perf_counter() - debut


@contextmanager
def fichier_chronometre(
    chemin: str | Path,
    mode: str = "r",
    *,
    journal: Callable[[str], None] = print,
) -> Iterator[IO[Any]]:
    """L'exercice du cours, version ``@contextmanager`` : mêmes messages, dans
    le même ordre, que ``FichierChronometre`` à l'étape 4."""
    fichier = open(chemin, mode, encoding="utf-8")  # noqa: SIM115
    debut = time.perf_counter()
    try:
        yield fichier
    except Exception as e:
        journal(f"Erreur pendant l'utilisation de {chemin} : {e!r}")
        raise
    finally:
        fichier.close()
        duree = time.perf_counter() - debut
        journal(f"{chemin} fermé après {duree:.3f} s")


@contextmanager
def transaction[V](donnees: dict[str, V]) -> Iterator[dict[str, V]]:
    """La ``Transaction`` de l'étape 4 en générateur : si le bloc lève une
    ``Exception``, le dictionnaire retrouve sur place son contenu d'entrée et
    l'exception se propage."""
    copie = dict(donnees)
    try:
        yield donnees
    except Exception:
        donnees.clear()
        donnees.update(copie)
        raise


class Emetteur:
    """Produit du code indenté, comme le générateur de code du langage.

    e = Emetteur()
    e.ligne("def f():")
    with e.bloc():
        e.ligne("return 1")
    """

    def __init__(self, indentation: str = "    ") -> None:
        self.indentation = indentation
        self.niveau = 0
        self._lignes: list[str] = []

    def ligne(self, texte: str = "") -> None:
        """Ajoute une ligne au niveau courant. Une ligne vide reste vide (pas
        d'espaces en fin de ligne)."""
        self._lignes.append(self.indentation * self.niveau + texte if texte else "")

    @contextmanager
    def bloc(self, vide: str | None = "pass") -> Iterator[None]:
        """Augmente l'indentation pour la durée du ``with``, et la rétablit en
        sortie, même en cas d'exception. Si rien n'a été émis dans le bloc et
        que ``vide`` n'est pas ``None``, émet ``vide`` dans le bloc."""
        avant = len(self._lignes)
        self.niveau += 1
        try:
            yield
            if len(self._lignes) == avant and vide is not None:
                self.ligne(vide)
        finally:
            self.niveau -= 1

    def texte(self) -> str:
        """Les lignes jointes par ``"\\n"``, avec un ``"\\n"`` final (chaîne
        vide si rien n'a été émis)."""
        return "\n".join(self._lignes) + "\n" if self._lignes else ""


@dataclass
class Portee:
    nom: str
    noms: dict[str, object] = field(default_factory=dict)


class TableSymboles:
    """Une pile de portées, comme l'analyse sémantique du langage. La
    première, ``"globale"``, n'est jamais retirée."""

    def __init__(self) -> None:
        self._portees = [Portee("globale")]

    @property
    def courante(self) -> Portee:
        return self._portees[-1]

    @property
    def profondeur(self) -> int:
        """Nombre de portées ouvertes, la globale comprise."""
        return len(self._portees)

    def declarer(self, nom: str, valeur: object) -> None:
        self.courante.noms[nom] = valeur

    def chercher(self, nom: str) -> object:
        """Cherche ``nom`` de la portée courante vers la globale. Lève
        ``KeyError`` s'il n'est déclaré nulle part."""
        for portee in reversed(self._portees):
            if nom in portee.noms:
                return portee.noms[nom]
        raise KeyError(nom)

    @contextmanager
    def portee(self, nom: str = "bloc") -> Iterator[Portee]:
        """Ouvre une nouvelle portée pour la durée du ``with`` et la lie à
        ``as`` ; la retire en sortie, même en cas d'exception."""
        nouvelle = Portee(nom)
        self._portees.append(nouvelle)
        try:
            yield nouvelle
        finally:
            self._portees.pop()

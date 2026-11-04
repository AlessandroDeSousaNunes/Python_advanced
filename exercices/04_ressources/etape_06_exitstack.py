"""Étape 6 : les outils de ``contextlib``.

``suppress``, ``closing``, ``nullcontext`` et ``ExitStack`` : des context
managers prêts à l'emploi, et un moyen d'en composer un nombre variable.
"""

import os
from collections.abc import Callable
from contextlib import (
    AbstractContextManager,
    ExitStack,
    closing,
    nullcontext,
    suppress,
)
from pathlib import Path
from typing import IO, Any

from etape_03_nettoyage import Ressource


def supprimer_si_present(chemin: str | Path) -> bool:
    """Supprime le fichier et renvoie ``True`` ; renvoie ``False`` s'il
    n'existe pas. Toute autre ``OSError`` se propage. Sans ``try``."""
    with suppress(FileNotFoundError):
        os.remove(chemin)
        return True
    return False


class Lecteur:
    """Un objet qui se ferme avec ``close()`` mais n'est **pas** un context
    manager. Fourni."""

    def __init__(self, lignes: list[str]) -> None:
        self._lignes = iter(lignes)
        self.ferme = False

    def readline(self) -> str:
        if self.ferme:
            raise ValueError("lecteur fermé")
        return next(self._lignes, "")

    def close(self) -> None:
        self.ferme = True


def premiere_ligne(lecteur: Lecteur) -> str:
    """Renvoie la première ligne du lecteur, sans son ``"\\n"`` final, et
    ferme le lecteur dans tous les cas, avec ``contextlib.closing``."""
    with closing(lecteur) as l:  # noqa: E741
        return l.readline().removesuffix("\n")


def proteger(
    verrou: AbstractContextManager[object] | None,
) -> AbstractContextManager[object]:
    """Renvoie ``verrou``, ou un context manager neutre (``nullcontext``) si
    ``verrou`` vaut ``None`` : l'appelant écrit toujours ``with proteger(v):``."""
    if verrou is None:
        return nullcontext()
    return verrou


def incrementer(
    compteurs: dict[str, int],
    cle: str,
    verrou: AbstractContextManager[object] | None = None,
) -> int:
    """Incrémente ``compteurs[cle]`` (0 si absente) à l'intérieur de
    ``with proteger(verrou):`` et renvoie la nouvelle valeur."""
    with proteger(verrou):
        compteurs[cle] = compteurs.get(cle, 0) + 1
        return compteurs[cle]


def concatener(sources: list[str | Path], destination: str | Path) -> int:
    """Ouvre **toutes** les sources (en lecture), puis la destination (en
    écriture), avec un seul ``ExitStack`` ; recopie les sources l'une après
    l'autre, ligne par ligne, et renvoie le nombre de lignes écrites. Tous les
    fichiers sont ouverts avec ``encoding="utf-8"``. Si une source manque, la
    destination n'est pas créée et les sources déjà ouvertes sont fermées."""
    with ExitStack() as pile:
        fichiers = [
            pile.enter_context(open(source, encoding="utf-8")) for source in sources
        ]
        sortie = pile.enter_context(open(destination, "w", encoding="utf-8"))
        nombre = 0
        for fichier in fichiers:
            for ligne in fichier:
                sortie.write(ligne)
                nombre += 1
        return nombre


def ouvrir_tous(chemins: list[str | Path]) -> tuple[list[IO[Any]], ExitStack]:
    """Ouvre tous les fichiers en lecture (``encoding="utf-8"``). Si une
    ouverture échoue, ceux déjà ouverts sont fermés et l'erreur se propage.
    Sinon, renvoie les fichiers **ouverts** et la pile qui les fermera :
    l'appelant en devient responsable (``with pile:``)."""
    with ExitStack() as pile:
        fichiers = [
            pile.enter_context(open(chemin, encoding="utf-8")) for chemin in chemins
        ]
        # pop_all transfère les fermetures à une nouvelle pile : la sortie du
        # with ne ferme donc rien, c'est l'appelant qui s'en chargera.
        return fichiers, pile.pop_all()


def avec_ressources[T](
    ressources: list[Ressource], action: Callable[[list[Ressource]], T]
) -> T:
    """``avec_ressources`` de l'étape 3, réécrite avec ``ExitStack`` et
    ``callback`` : ouvre dans l'ordre, ferme celles qui ont été ouvertes dans
    l'ordre inverse, même en cas d'erreur."""
    with ExitStack() as pile:
        for ressource in ressources:
            ressource.ouvrir()
            pile.callback(ressource.fermer)
        return action(ressources)

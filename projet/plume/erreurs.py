"""Positions dans le source, erreurs de Plume et leur mise en forme."""

from collections.abc import Sequence
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Position:
    """Une position dans le source, numérotée à partir de 1 comme dans un
    éditeur. ``Position(0, 0)`` sert de position inconnue."""

    ligne: int
    colonne: int

    def __str__(self) -> str:
        return f"ligne {self.ligne}, colonne {self.colonne}"


SANS_POSITION = Position(0, 0)


class ErreurPlume(Exception):
    """Racine de toutes les erreurs de Plume."""

    genre = "erreur"

    def __init__(self, message: str, position: Position | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.position = position

    def __str__(self) -> str:
        if self.position is None:
            return self.message
        return f"{self.message} ({self.position})"


class ErreurLexicale(ErreurPlume):
    genre = "erreur lexicale"


class ErreurSyntaxe(ErreurPlume):
    genre = "erreur de syntaxe"


class ErreurSemantique(ErreurPlume):
    genre = "erreur sémantique"


class ErreurExecution(ErreurPlume):
    genre = "erreur d'exécution"


class ErreurBackend(ErreurPlume):
    genre = "erreur"


class ErreursMultiples(ErreurPlume):
    """Plusieurs erreurs trouvées en une seule passe (parser, analyse)."""

    genre = "erreurs"

    def __init__(self, erreurs: Sequence[ErreurPlume]) -> None:
        self.erreurs = list(erreurs)
        premiere = self.erreurs[0].position if self.erreurs else None
        super().__init__(f"{len(self.erreurs)} erreur(s)", premiere)

    def __str__(self) -> str:
        return "\n".join(str(erreur) for erreur in self.erreurs)


def formater(erreur: ErreurPlume, source: str, fichier: str = "<source>") -> str:
    """Un message prêt à afficher : ``fichier:ligne:colonne : genre : message``,
    puis la ligne fautive et un ``^`` sous la colonne. Une ``ErreursMultiples``
    donne un bloc par erreur."""
    if isinstance(erreur, ErreursMultiples):
        return "\n".join(formater(e, source, fichier) for e in erreur.erreurs)
    pos = erreur.position
    if pos is None or pos == SANS_POSITION:
        return f"{fichier} : {erreur.genre} : {erreur.message}"
    entete = f"{fichier}:{pos.ligne}:{pos.colonne} : {erreur.genre} : {erreur.message}"
    lignes = source.splitlines()
    if not 1 <= pos.ligne <= len(lignes):
        return entete
    return f"{entete}\n    {lignes[pos.ligne - 1]}\n    {' ' * (pos.colonne - 1)}^"

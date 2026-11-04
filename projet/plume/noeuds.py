"""Les nœuds de l'arbre syntaxique (AST) de Plume.

Chaque nœud a un champ ``pos`` (sa position dans le source), exclu de la
comparaison et du ``repr`` : deux arbres de même forme sont égaux, où qu'ils
soient écrits.
"""

from dataclasses import dataclass, field, fields, is_dataclass
from typing import Any

from plume.erreurs import SANS_POSITION, Position

type Expr = Entier | Texte | Booleen | Variable | Unaire | Binaire | Appel
type Instr = (
    Declaration | Affectation | Affiche | Si | TantQue | Fonction | Retourne | ExprInstr
)


def _pos() -> Any:
    """Le champ ``pos`` : facultatif, nommé, hors comparaison et hors ``repr``.
    (Un objet ``field`` ne peut pas être partagé entre classes, d'où la
    fonction.)"""
    return field(default=SANS_POSITION, compare=False, repr=False, kw_only=True)


# --- Expressions --------------------------------------------------------------


@dataclass(frozen=True)
class Entier:
    valeur: int
    pos: Position = _pos()


@dataclass(frozen=True)
class Texte:
    valeur: str
    pos: Position = _pos()


@dataclass(frozen=True)
class Booleen:
    valeur: bool
    pos: Position = _pos()


@dataclass(frozen=True)
class Variable:
    nom: str
    pos: Position = _pos()


@dataclass(frozen=True)
class Unaire:
    operateur: str  # "-" ou "non"
    operande: Expr
    pos: Position = _pos()


@dataclass(frozen=True)
class Binaire:
    operateur: str  # "+", "et", "==", ...
    gauche: Expr
    droite: Expr
    pos: Position = _pos()


@dataclass(frozen=True)
class Appel:
    fonction: str
    arguments: tuple[Expr, ...]
    pos: Position = _pos()


# --- Instructions -------------------------------------------------------------


@dataclass(frozen=True)
class Declaration:
    nom: str
    valeur: Expr
    pos: Position = _pos()


@dataclass(frozen=True)
class Affectation:
    nom: str
    valeur: Expr
    pos: Position = _pos()


@dataclass(frozen=True)
class Affiche:
    valeurs: tuple[Expr, ...]
    pos: Position = _pos()


@dataclass(frozen=True)
class Si:
    condition: Expr
    alors: tuple[Instr, ...]
    sinon: tuple[Instr, ...] | None = None
    pos: Position = _pos()


@dataclass(frozen=True)
class TantQue:
    condition: Expr
    corps: tuple[Instr, ...]
    pos: Position = _pos()


@dataclass(frozen=True)
class Fonction:
    nom: str
    parametres: tuple[str, ...]
    corps: tuple[Instr, ...]
    pos: Position = _pos()


@dataclass(frozen=True)
class Retourne:
    valeur: Expr | None = None
    pos: Position = _pos()


@dataclass(frozen=True)
class ExprInstr:
    """Une expression utilisée comme instruction : ``saluer("Ada");``."""

    expression: Expr
    pos: Position = _pos()


@dataclass(frozen=True)
class Programme:
    instructions: tuple[Instr, ...]
    pos: Position = _pos()


# --- Affichage de l'arbre -----------------------------------------------------


def afficher_arbre(noeud: object) -> str:
    """L'arbre indenté, un nœud par ligne, avec le nom de chaque champ. Marche
    pour tous les nœuds, sans code propre à chacun."""
    lignes: list[str] = []
    _afficher(noeud, 0, "", lignes)
    return "\n".join(lignes)


def _afficher(valeur: object, niveau: int, etiquette: str, lignes: list[str]) -> None:
    prefixe = "  " * niveau + (f"{etiquette}: " if etiquette else "")
    if is_dataclass(valeur) and not isinstance(valeur, type):
        lignes.append(prefixe + type(valeur).__name__)
        for champ in fields(valeur):
            if champ.name != "pos":
                _afficher(getattr(valeur, champ.name), niveau + 1, champ.name, lignes)
    elif isinstance(valeur, tuple) and valeur:
        lignes.append(prefixe.rstrip())
        for element in valeur:
            _afficher(element, niveau + 1, "", lignes)
    else:
        lignes.append(prefixe + repr(valeur))

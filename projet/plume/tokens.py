"""Les types de token de Plume.

Un token, c'est UN MOT du programme, avec une étiquette qui dit quelle sorte de
mot c'est. Pour ``soit x = 2;``, le lexer produit 5 tokens (plus FIN) :

    soit   ->  étiquette SOIT           (un mot-clé)
    x      ->  étiquette IDENT          (un nom choisi par l'utilisateur)
    =      ->  étiquette EGAL           (un symbole)
    2      ->  étiquette ENTIER         (un nombre)
    ;      ->  étiquette POINT_VIRGULE  (un symbole)

``TokenKind`` est la liste de toutes les étiquettes possibles ; ``Token`` est
la petite fiche qui réunit le mot, son étiquette et sa position.
"""

from dataclasses import dataclass, field
from enum import Enum

from plume.erreurs import Position


class TokenKind(Enum):
    """Toutes les étiquettes possibles d'un token. Une ``Enum`` est une liste
    fermée : un token ne peut pas avoir une étiquette qui n'est pas ici."""

    # Littéraux et identifiants : la valeur sert seulement aux messages.
    ENTIER = "<entier>"
    TEXTE = "<texte>"
    IDENT = "<identifiant>"
    FIN = "<fin>"

    # Mots-clés : la valeur est l'orthographe dans le source.
    SOIT = "soit"
    SI = "si"
    SINON = "sinon"
    TANTQUE = "tantque"
    FONCTION = "fonction"
    RETOURNE = "retourne"
    AFFICHE = "affiche"
    VRAI = "vrai"
    FAUX = "faux"
    ET = "et"
    OU = "ou"
    NON = "non"

    # Symboles.
    PLUS = "+"
    MOINS = "-"
    FOIS = "*"
    DIVISE = "/"
    MODULO = "%"
    EGAL_EGAL = "=="
    DIFFERENT = "!="
    INFERIEUR = "<"
    INFERIEUR_EGAL = "<="
    SUPERIEUR = ">"
    SUPERIEUR_EGAL = ">="
    EGAL = "="
    PAR_OUVRANTE = "("
    PAR_FERMANTE = ")"
    ACC_OUVRANTE = "{"
    ACC_FERMANTE = "}"
    VIRGULE = ","
    POINT_VIRGULE = ";"

    @property
    def est_special(self) -> bool:
        """Littéral, identifiant ou fin : ni mot-clé ni symbole."""
        return self in SPECIAUX

    @property
    def est_mot_cle(self) -> bool:
        return not self.est_special and self.value.isalpha()

    @property
    def est_symbole(self) -> bool:
        return not self.est_special and not self.value.isalpha()

    def __str__(self) -> str:
        """``';'`` pour un symbole ou un mot-clé, ``<identifiant>`` sinon."""
        return self.value if self.est_special else f"'{self.value}'"


SPECIAUX = frozenset(
    {TokenKind.ENTIER, TokenKind.TEXTE, TokenKind.IDENT, TokenKind.FIN}
)

#: Orthographe -> type, construit à partir de l'Enum.
MOTS_CLES: dict[str, TokenKind] = {k.value: k for k in TokenKind if k.est_mot_cle}

#: Du plus long au plus court : le lexer essaie ``==`` avant ``=``.
SYMBOLES: list[TokenKind] = sorted(
    (k for k in TokenKind if k.est_symbole), key=lambda k: len(k.value), reverse=True
)


@dataclass(frozen=True, slots=True)
class Token:
    """Un token : son type, son lexème et sa position. Pour un texte, le
    lexème est déjà décodé (sans guillemets ni échappements) ; ``taille``
    garde alors sa longueur dans le source.

    ``frozen=True`` : une fois créé, un token ne peut plus être modifié."""

    kind: TokenKind  # l'étiquette : SOIT, IDENT, ENTIER, PLUS…
    lexeme: str  # le texte exact du mot : "soit", "x", "2"…
    position: Position  # où il se trouve : ligne et colonne
    taille: int = field(default=-1, compare=False)

    @property
    def fin(self) -> Position:
        """La position juste après le token."""
        taille = len(self.lexeme) if self.taille < 0 else self.taille
        return Position(self.position.ligne, self.position.colonne + taille)

    def __repr__(self) -> str:
        p = self.position
        return f"Token({self.kind.name}, {self.lexeme!r}, {p.ligne}:{p.colonne})"

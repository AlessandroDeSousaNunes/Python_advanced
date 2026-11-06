"""Les formes des réponses des outils (``TypedDict``).

Annoter un outil ``-> ResultatCheck`` suffit : le SDK en calcule le schéma de
sortie. L'IA sait donc à l'avance quels champs elle recevra.

Pas de ``from __future__ import annotations`` ici : le SDK lit ces types à
l'exécution pour construire les schémas.
"""

from typing import Literal, TypedDict


class ErreurJSON(TypedDict):
    genre: str  # "erreur lexicale", "erreur de syntaxe"…
    message: str
    ligne: int | None
    colonne: int | None
    contexte: str  # le message complet, avec la ligne fautive et un ^


class TokenJSON(TypedDict):
    type: str
    texte: str
    ligne: int
    colonne: int


class ResultatTokenize(TypedDict):
    ok: bool
    tokens: list[TokenJSON]
    erreurs: list[ErreurJSON]


class ResultatParse(TypedDict):
    ok: bool
    arbre: dict[str, object] | None
    erreurs: list[ErreurJSON]


class ResultatCheck(TypedDict):
    ok: bool
    erreurs: list[ErreurJSON]


class ResultatTranspile(TypedDict):
    ok: bool
    code: str
    correspondances: dict[str, list[int]] | None  # ligne Python -> [ligne, colonne]
    erreurs: list[ErreurJSON]


class ResultatFormat(TypedDict):
    ok: bool
    code: str
    modifie: bool
    avertissement: str | None
    erreurs: list[ErreurJSON]


type Statut = Literal[
    "ok",
    "erreur_compilation",
    "erreur_execution",
    "delai_depasse",
    "sortie_tronquee",
    "memoire_depassee",
    "erreur_interne",
]


class ResultatRun(TypedDict):
    statut: Statut
    sortie: str
    erreurs: list[ErreurJSON]
    duree: float

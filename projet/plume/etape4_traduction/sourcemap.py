"""Extension 13 : la source map.

Une source map, c'est un petit annuaire : pour chaque ligne du Python généré,
elle dit de quelle ligne (et colonne) du programme Plume elle vient.

    ligne Python 10  ->  ligne Plume 3, colonne 5

Elle sert quand Python plante : Python dit « erreur ligne 10 », la source map
répond « c'est la ligne 3 de ton programme Plume ».

On peut :

- la DÉCALER : le prélude (la petite fonction ``_texte``) est ajouté avant le
  code de l'utilisateur, donc toutes les lignes Python descendent d'autant ;
- l'ENREGISTRER en JSON à côté du fichier généré (``programme.py.map.json``) ;
- la RELIRE depuis ce JSON.
"""

from dataclasses import dataclass, field
from typing import Literal, Self, TypedDict

from plume.erreurs import Position

#: La seule version du format que l'on sait lire.
VERSION = 1


class SourceMapJSON(TypedDict):
    """La forme JSON de la source map."""

    version: Literal[1]
    source: str  # le nom du fichier Plume
    # JSON n'a que des clés texte : "10" -> [3, 5] (ligne, colonne Plume)
    lignes: dict[str, list[int]]


@dataclass(frozen=True, slots=True)
class SourceMap:
    """ligne du Python généré -> position dans le programme Plume."""

    source: str = "<source>"
    lignes: dict[int, Position] = field(default_factory=dict)

    def position(self, ligne_python: int) -> Position | None:
        """La position Plume d'une ligne Python, ou ``None`` (prélude…)."""
        return self.lignes.get(ligne_python)

    def ligne_source(self, ligne_python: int) -> int | None:
        """La ligne Plume d'une ligne Python, ou ``None``."""
        position = self.position(ligne_python)
        return None if position is None else position.ligne

    def decaler(self, decalage: int) -> "SourceMap":
        """Toutes les lignes Python descendent de ``decalage`` ; les lignes
        Plume, elles, ne bougent pas."""
        lignes = {ligne + decalage: pos for ligne, pos in self.lignes.items()}
        return SourceMap(self.source, lignes)

    def renommer(self, source: str) -> "SourceMap":
        """La même source map, pour un autre nom de fichier Plume."""
        return SourceMap(source, dict(self.lignes))

    def vers_json(self) -> SourceMapJSON:
        return {
            "version": 1,
            "source": self.source,
            "lignes": {
                str(ligne): [pos.ligne, pos.colonne]
                for ligne, pos in sorted(self.lignes.items())
            },
        }

    @classmethod
    def depuis_json(cls, donnees: SourceMapJSON) -> Self:
        """Le constructeur inverse de ``vers_json``. Refuse une version
        inconnue : on ne devine pas un format qu'on ne connaît pas."""
        if donnees.get("version") != VERSION:
            raise ValueError(
                f"version de source map inconnue : {donnees.get('version')!r}"
            )
        lignes = {
            int(ligne): Position(pos[0], pos[1])
            for ligne, pos in donnees["lignes"].items()
        }
        return cls(donnees["source"], lignes)

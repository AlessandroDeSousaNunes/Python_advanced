"""Le contrat d'un backend : ce qui transforme un arbre analysé en code."""

from dataclasses import dataclass, field
from typing import Protocol

from plume.erreurs import Position
from plume.noeuds import Programme
from plume.semantique import Analyse


@dataclass(frozen=True, slots=True)
class Sortie:
    """Le code produit, et pour chaque ligne la position Plume d'origine."""

    code: str
    correspondances: dict[int, Position] = field(default_factory=dict)


class Backend(Protocol):
    nom: str
    extension: str
    executable: bool  # le code produit est-il du Python exécutable ?

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie: ...

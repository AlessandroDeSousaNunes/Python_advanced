"""Le contrat d'un backend : ce qui transforme un arbre analysé en code."""

from dataclasses import dataclass
from typing import Protocol

from plume.etape2_parser.noeuds import Programme
from plume.etape3_analyse.semantique import Analyse
from plume.etape4_traduction.sourcemap import SourceMap


@dataclass(frozen=True, slots=True)
class Sortie:
    """Le code produit et, pour un backend Python, sa source map
    (ligne Python -> position Plume). ``None`` pour les autres backends."""

    code: str
    sourcemap: SourceMap | None = None


class Backend(Protocol):
    nom: str
    extension: str
    executable: bool  # le code produit est-il du Python exécutable ?

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie: ...

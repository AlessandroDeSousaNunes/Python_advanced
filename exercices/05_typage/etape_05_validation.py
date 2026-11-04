"""Étape 5 : dataclasses, validation et pipeline.

L'exercice du cours : un ``Pipeline`` qui accepte n'importe quelle ``Source``
(injectée), convertit chaque enregistrement brut en ``Mesure`` validée, et
garde les rejets au lieu de s'arrêter au premier.
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal, Self, TypeGuard, get_args

from etape_04_sources import Brut, Source

Unite = Literal["C", "%", "hPa"]

BORNES: dict[Unite, tuple[float, float]] = {
    "C": (-90.0, 60.0),
    "%": (0.0, 100.0),
    "hPa": (870.0, 1085.0),
}


def est_unite(valeur: object) -> TypeGuard[Unite]:
    """Vrai si ``valeur`` est l'une des unités de ``Unite``."""
    return isinstance(valeur, str) and valeur in get_args(Unite)


class MesureInvalide(ValueError):
    """Une mesure invalide. ``champ`` nomme le champ fautif."""

    def __init__(self, champ: str, message: str) -> None:
        self.champ = champ
        super().__init__(f"{champ} : {message}")


@dataclass(frozen=True)
class Mesure:
    capteur: str
    valeur: float
    unite: Unite

    def __post_init__(self) -> None:
        """Valide la mesure, champ par champ, et lève ``MesureInvalide`` :
        capteur non vide, unité connue, valeur numérique finie (pas un
        booléen) et comprise dans ``BORNES[unite]``."""
        # Les annotations ne sont pas vérifiées à l'exécution : on relit les
        # champs comme des « object » pour pouvoir tout tester.
        capteur: object = self.capteur
        unite: object = self.unite
        valeur: object = self.valeur
        if not isinstance(capteur, str) or not capteur.strip():
            raise MesureInvalide("capteur", "texte non vide attendu")
        if not est_unite(unite):
            raise MesureInvalide("unite", f"unité inconnue {unite!r}")
        if (
            not isinstance(valeur, (int, float))
            or isinstance(valeur, bool)
            or not math.isfinite(valeur)
        ):
            raise MesureInvalide("valeur", "nombre fini attendu")
        minimum, maximum = BORNES[unite]
        if not minimum <= valeur <= maximum:
            raise MesureInvalide("valeur", f"{valeur} hors de [{minimum}, {maximum}]")

    @classmethod
    def depuis_brut(cls, brut: Mapping[str, object]) -> Self:
        """Convertit un enregistrement brut : les valeurs d'un CSV sont des
        chaînes (``" 21,5 "`` accepté), celles d'un JSON déjà des nombres.
        Les espaces autour du capteur sont retirés."""
        for champ in ("capteur", "valeur", "unite"):
            if champ not in brut:
                raise MesureInvalide(champ, "champ manquant")

        capteur = brut["capteur"]
        if not isinstance(capteur, str):
            raise MesureInvalide("capteur", "texte attendu")

        valeur_brute = brut["valeur"]
        if isinstance(valeur_brute, str):
            try:
                valeur = float(valeur_brute.strip().replace(",", "."))
            except ValueError as e:
                raise MesureInvalide("valeur", f"nombre illisible {valeur_brute!r}") from e
        elif isinstance(valeur_brute, (int, float)) and not isinstance(valeur_brute, bool):
            valeur = float(valeur_brute)
        else:
            raise MesureInvalide("valeur", "nombre attendu")

        unite = brut["unite"]
        if not est_unite(unite):
            raise MesureInvalide("unite", f"unité inconnue {unite!r}")

        return cls(capteur.strip(), valeur, unite)


@dataclass(frozen=True)
class Rejet:
    numero: int
    """Rang de l'enregistrement dans la source, à partir de 1."""
    brut: Brut
    erreur: MesureInvalide


@dataclass
class Rapport:
    source: str
    valides: list[Mesure] = field(default_factory=list)
    rejets: list[Rejet] = field(default_factory=list)

    @property
    def taux_rejet(self) -> float:
        """Part des enregistrements rejetés (0.0 si la source est vide)."""
        nombre = len(self.valides) + len(self.rejets)
        if nombre == 0:
            return 0.0
        return len(self.rejets) / nombre


class TropDeRejets(Exception):
    def __init__(self, rapport: Rapport) -> None:
        self.rapport = rapport
        super().__init__(f"{rapport.source} : trop de rejets ({len(rapport.rejets)})")


class Pipeline:
    def __init__(self, source: Source, *, max_rejets: int | None = None) -> None:
        self.source = source
        self.max_rejets = max_rejets

    def executer(self) -> Rapport:
        """Lit toute la source et renvoie le rapport. Lève ``TropDeRejets``
        dès que le nombre de rejets dépasse ``max_rejets``. La source est
        fermée dans tous les cas."""
        rapport = Rapport(self.source.nom)
        try:
            for numero, brut in enumerate(self.source.lire(), start=1):
                try:
                    rapport.valides.append(Mesure.depuis_brut(brut))
                except MesureInvalide as e:
                    rapport.rejets.append(Rejet(numero, brut, e))
                    if self.max_rejets is not None and len(rapport.rejets) > self.max_rejets:
                        raise TropDeRejets(rapport) from e
        finally:
            self.source.fermer()
        return rapport

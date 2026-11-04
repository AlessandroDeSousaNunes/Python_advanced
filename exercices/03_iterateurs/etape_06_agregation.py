"""Étape 6 : agréger un flux de ventes.

Cette étape utilise ``Vente`` et ``ventes`` de l'étape 5. Seul
``rapport_par_region`` a besoin que l'étape 5 soit terminée.
"""

import heapq
import math
from collections.abc import Callable, Iterable, Iterator
from dataclasses import dataclass
from functools import reduce
from itertools import groupby
from pathlib import Path

import etape_05_lecteur_csv as etape_05
from etape_05_lecteur_csv import Vente

#: Une clé de regroupement : reçoit une vente, renvoie le nom de son groupe.
Cle = Callable[[Vente], str]


@dataclass(frozen=True)
class Resume:
    """Résumé d'une série de valeurs, calculé en un seul passage."""

    nombre: int = 0
    total: float = 0.0
    minimum: float = math.inf
    maximum: float = -math.inf

    def ajouter(self, valeur: float) -> "Resume":
        """Renvoie un **nouveau** résumé qui tient compte de ``valeur``."""
        return Resume(
            self.nombre + 1,
            self.total + valeur,
            min(self.minimum, valeur),
            max(self.maximum, valeur),
        )

    @property
    def moyenne(self) -> float:
        """Moyenne des valeurs. ``ValueError`` si le résumé est vide."""
        if self.nombre == 0:
            raise ValueError("résumé vide : pas de moyenne")
        return self.total / self.nombre


def resumer(valeurs: Iterable[float]) -> Resume:
    """Résume ``valeurs`` en un seul passage, avec ``functools.reduce``."""
    return reduce(lambda resume, valeur: resume.ajouter(valeur), valeurs, Resume())


def resumer_par(ventes: Iterable[Vente], cle: Cle) -> dict[str, Resume]:
    """Résume les montants des ventes de chaque groupe, en un seul passage.
    Les groupes apparaissent dans l'ordre de leur première vente."""
    resumes: dict[str, Resume] = {}
    for vente in ventes:
        groupe = cle(vente)
        resumes[groupe] = resumes.get(groupe, Resume()).ajouter(vente.montant)
    return resumes


def grouper_par(ventes: Iterable[Vente], cle: Cle) -> dict[str, list[Vente]]:
    """Regroupe les ventes avec ``sorted`` puis ``itertools.groupby``. Les
    groupes sont dans l'ordre alphabétique, et les ventes de chaque groupe
    dans leur ordre d'origine."""
    # sorted est stable : à clé égale, l'ordre d'origine est conservé.
    triees = sorted(ventes, key=cle)
    return {groupe: list(elements) for groupe, elements in groupby(triees, key=cle)}


def cumuls_journaliers(ventes: Iterable[Vente]) -> Iterator[tuple[str, float]]:
    """Pour des ventes **triées par date**, produit ``(date, cumul)`` : le
    montant cumulé depuis le début, à la fin de chaque journée. Paresseux."""
    cumul = 0.0
    for date, du_jour in groupby(ventes, key=lambda vente: vente.date):
        cumul += sum(vente.montant for vente in du_jour)
        yield date, cumul


def meilleures(ventes: Iterable[Vente], n: int) -> list[Vente]:
    """Les ``n`` ventes de plus fort montant, de la plus forte à la plus
    faible (à montant égal, dans l'ordre d'origine)."""
    return heapq.nlargest(n, ventes, key=lambda vente: vente.montant)


def rapport_par_region(chemin: str | Path) -> dict[str, Resume]:
    """Lit le fichier avec ``ventes`` (étape 5) et résume les montants de
    chaque région."""
    return resumer_par(etape_05.ventes(chemin), lambda vente: vente.region)

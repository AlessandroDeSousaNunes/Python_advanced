"""Étape 5 : lecteur CSV paresseux.

Chaque étage du pipeline est un générateur : le fichier est lu ligne par
ligne, et rien n'est jamais chargé en entier.

    lire_lignes  →  convertir  →  filtrer  →  (somme, comptage…)
"""

import csv
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass(frozen=True)
class Vente:
    """Une ligne du fichier, convertie. Fournie."""

    date: str
    region: str
    produit: str
    quantite: int
    prix_unitaire: float

    @property
    def montant(self) -> float:
        return self.quantite * self.prix_unitaire


class Compteur[T]:
    """Itérateur qui laisse passer les éléments de ``source`` en les comptant
    dans l'attribut ``nombre``."""

    def __init__(self, source: Iterable[T]) -> None:
        self._source = iter(source)
        self.nombre = 0

    def __iter__(self) -> Self:
        return self

    def __next__(self) -> T:
        element = next(self._source)  # StopIteration remonte toute seule
        self.nombre += 1
        return element


def lire_lignes(chemin: str | Path) -> Iterator[dict[str, str]]:
    """Produit chaque ligne du fichier CSV sous forme de dictionnaire
    (``csv.DictReader``), en ignorant les lignes dont toutes les valeurs sont
    vides. Le fichier est ouvert avec ``open(chemin, newline="",
    encoding="utf-8")`` et fermé dès que le générateur se termine ou est
    fermé."""
    with open(chemin, newline="", encoding="utf-8") as fichier:
        for ligne in csv.DictReader(fichier):
            if any(valeur for valeur in ligne.values()):
                yield ligne


def convertir(
    lignes: Iterable[dict[str, str]],
    rejets: list[dict[str, str]] | None = None,
) -> Iterator[Vente]:
    """Convertit chaque ligne en ``Vente``. Une ligne invalide (colonne
    manquante, quantité ou prix illisible) est ignorée, et ajoutée à
    ``rejets`` si cette liste est fournie."""
    for ligne in lignes:
        try:
            vente = Vente(
                ligne["date"],
                ligne["region"],
                ligne["produit"],
                int(ligne["quantite"]),
                float(ligne["prix_unitaire"]),
            )
        except (KeyError, ValueError, TypeError):
            if rejets is not None:
                rejets.append(ligne)
            continue
        yield vente


def filtrer(
    ventes: Iterable[Vente],
    *,
    region: str | None = None,
    montant_min: float = 0.0,
) -> Iterator[Vente]:
    """Garde les ventes de ``region`` (toutes si ``None``) dont le montant est
    au moins ``montant_min``. Une expression génératrice suffit."""
    return (
        vente
        for vente in ventes
        if (region is None or vente.region == region) and vente.montant >= montant_min
    )


def ventes(
    chemin: str | Path,
    *,
    region: str | None = None,
    montant_min: float = 0.0,
    rejets: list[dict[str, str]] | None = None,
) -> Iterator[Vente]:
    """Le pipeline complet : lire, convertir, filtrer."""
    lignes = lire_lignes(chemin)
    converties = convertir(lignes, rejets)
    return filtrer(converties, region=region, montant_min=montant_min)


def montant_total(
    chemin: str | Path, *, region: str | None = None, montant_min: float = 0.0
) -> float:
    """Somme des montants des ventes retenues par ``ventes``."""
    return sum(
        vente.montant
        for vente in ventes(chemin, region=region, montant_min=montant_min)
    )

"""Étape 6 : refactoring SOLID.

``RapportCapteurs`` (fourni) fait tout : il lit le CSV, valide, calcule,
formate et écrit le fichier. On le découpe en pièces qui ont chacune une
seule responsabilité (SRP), et un ``ServiceRapport`` qui ne dépend que
d'abstractions (DIP). Ajouter un format ne demande alors aucune modification
du service (OCP).
"""

import csv
import json
from collections.abc import Iterable, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

from etape_04_sources import Source
from etape_05_validation import Mesure, Pipeline, Unite

# --- Le code d'origine (fourni) -----------------------------------------------


class RapportCapteurs:
    """Tout-en-un : difficile à tester (il faut un vrai fichier), et chaque
    nouveau format oblige à modifier la classe."""

    def __init__(self, chemin_csv: str | Path, dossier: str | Path) -> None:
        self.chemin_csv = Path(chemin_csv)
        self.dossier = Path(dossier)

    def generer(self, sortie: str = "texte") -> Path:
        # 1. Lire et valider
        groupes: dict[str, list[float]] = {}
        unites: dict[str, str] = {}
        rejets = 0
        with open(self.chemin_csv, newline="", encoding="utf-8") as f:
            for ligne in csv.DictReader(f):
                try:
                    valeur = float(ligne["valeur"].replace(",", "."))
                except ValueError:
                    rejets += 1
                    continue
                capteur = ligne["capteur"].strip()
                if not capteur or ligne["unite"] not in ("C", "%", "hPa"):
                    rejets += 1
                    continue
                groupes.setdefault(capteur, []).append(valeur)
                unites[capteur] = ligne["unite"]
        # 2. Calculer et 3. formater
        if sortie == "texte":
            lignes = []
            for capteur in sorted(groupes):
                v = groupes[capteur]
                lignes.append(
                    f"{capteur} ({unites[capteur]}) : {len(v)} mesure(s), "
                    f"min {min(v)}, max {max(v)}, moyenne {sum(v) / len(v):.2f}"
                )
            lignes.append(f"Rejets : {rejets}")
            contenu = "\n".join(lignes) + "\n"
            extension = "txt"
        elif sortie == "json":
            contenu = json.dumps(
                {
                    "capteurs": [
                        {
                            "capteur": c,
                            "unite": unites[c],
                            "nombre": len(groupes[c]),
                            "minimum": min(groupes[c]),
                            "maximum": max(groupes[c]),
                            "moyenne": round(sum(groupes[c]) / len(groupes[c]), 2),
                        }
                        for c in sorted(groupes)
                    ],
                    "rejets": rejets,
                },
                ensure_ascii=False,
                indent=2,
            )
            extension = "json"
        else:
            raise ValueError(f"format inconnu : {sortie}")
        # 4. Écrire
        chemin = self.dossier / f"rapport.{extension}"
        chemin.write_text(contenu, encoding="utf-8")
        print(f"Rapport écrit dans {chemin}")
        return chemin


# --- Le calcul ----------------------------------------------------------------


@dataclass(frozen=True)
class Statistiques:
    capteur: str
    unite: Unite
    nombre: int
    minimum: float
    maximum: float
    moyenne: float


def calculer(mesures: Iterable[Mesure]) -> list[Statistiques]:
    """Une ``Statistiques`` par capteur, triées par nom de capteur. L'unité est
    celle de la dernière mesure du capteur ; la moyenne est arrondie à 2
    décimales."""
    valeurs: dict[str, list[float]] = {}
    unites: dict[str, Unite] = {}
    for mesure in mesures:
        valeurs.setdefault(mesure.capteur, []).append(mesure.valeur)
        unites[mesure.capteur] = mesure.unite  # la dernière gagne
    return [
        Statistiques(
            capteur,
            unites[capteur],
            len(valeurs[capteur]),
            min(valeurs[capteur]),
            max(valeurs[capteur]),
            round(sum(valeurs[capteur]) / len(valeurs[capteur]), 2),
        )
        for capteur in sorted(valeurs)
    ]


# --- La présentation ----------------------------------------------------------


class Formateur(Protocol):
    """Un attribut ``extension`` (texte, sans le point) et une méthode
    ``formater(statistiques, rejets)`` qui renvoie le contenu du rapport :
    ``statistiques`` est une séquence de ``Statistiques``, ``rejets`` un
    nombre."""

    extension: str

    def formater(self, statistiques: Sequence[Statistiques], rejets: int) -> str: ...


class FormateurTexte:
    """Exactement le format « texte » de ``RapportCapteurs``."""

    extension = "txt"

    def formater(self, statistiques: Sequence[Statistiques], rejets: int) -> str:
        lignes = [
            f"{s.capteur} ({s.unite}) : {s.nombre} mesure(s), "
            f"min {s.minimum}, max {s.maximum}, moyenne {s.moyenne:.2f}"
            for s in statistiques
        ]
        lignes.append(f"Rejets : {rejets}")
        return "\n".join(lignes) + "\n"


class FormateurJSON:
    """Le format « json » de ``RapportCapteurs``."""

    extension = "json"

    def formater(self, statistiques: Sequence[Statistiques], rejets: int) -> str:
        return json.dumps(
            {"capteurs": [asdict(s) for s in statistiques], "rejets": rejets},
            ensure_ascii=False,
            indent=2,
        )


class FormateurMarkdown:
    """Un tableau Markdown (voir le README), puis la ligne des rejets."""

    extension = "md"

    def formater(self, statistiques: Sequence[Statistiques], rejets: int) -> str:
        lignes = [
            "| capteur | unité | mesures | min | max | moyenne |",
            "|---|---|---|---|---|---|",
        ]
        for s in statistiques:
            lignes.append(
                f"| {s.capteur} | {s.unite} | {s.nombre} | "
                f"{s.minimum} | {s.maximum} | {s.moyenne} |"
            )
        lignes.append("")
        lignes.append(f"Rejets : {rejets}")
        return "\n".join(lignes) + "\n"


# --- Le stockage --------------------------------------------------------------


class Stockage(Protocol):
    """Une méthode ``enregistrer(nom, contenu)`` (deux textes) qui ne renvoie
    rien."""

    def enregistrer(self, nom: str, contenu: str) -> None: ...


class StockageMemoire:
    """Garde les contenus dans ``fichiers``, un ``dict`` nom -> contenu."""

    def __init__(self) -> None:
        self.fichiers: dict[str, str] = {}

    def enregistrer(self, nom: str, contenu: str) -> None:
        self.fichiers[nom] = contenu


class StockageDossier:
    """Écrit chaque contenu dans un fichier du dossier (``encoding="utf-8"``)."""

    def __init__(self, dossier: str | Path) -> None:
        self.dossier = Path(dossier)

    def enregistrer(self, nom: str, contenu: str) -> None:
        (self.dossier / nom).write_text(contenu, encoding="utf-8")


# --- Le service ---------------------------------------------------------------


class ServiceRapport:
    """Assemble les pièces. Il ne connaît aucune classe concrète de source, de
    formateur ni de stockage : on les lui injecte."""

    def __init__(
        self,
        source: Source,
        formateur: Formateur,
        stockage: Stockage,
        *,
        nom: str = "rapport",
    ) -> None:
        self.source = source
        self.formateur = formateur
        self.stockage = stockage
        self.nom = nom

    def produire(self) -> str:
        """Produit le rapport, l'enregistre et renvoie le nom du fichier
        (``"rapport.txt"``)."""
        rapport = Pipeline(self.source).executer()
        statistiques = calculer(rapport.valides)
        contenu = self.formateur.formater(statistiques, len(rapport.rejets))
        nom_fichier = f"{self.nom}.{self.formateur.extension}"
        self.stockage.enregistrer(nom_fichier, contenu)
        return nom_fichier

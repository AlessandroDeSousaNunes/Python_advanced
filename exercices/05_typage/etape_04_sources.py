"""Étape 4 : ``Protocol``, le typage structurel.

Des sources de données qui n'héritent de rien : il leur suffit d'avoir les
bonnes méthodes pour être acceptées partout où l'on attend une ``Source``.
"""

import csv
import json
from collections.abc import Iterable, Iterator, Mapping
from pathlib import Path
from typing import IO, Protocol, runtime_checkable

# Un enregistrement brut, tel qu'une source le lit.
Brut = dict[str, object]


class SourceInvalide(ValueError):
    """Le contenu d'une source n'a pas la forme attendue."""


@runtime_checkable
class Fermable(Protocol):
    """Tout objet qui a une méthode ``fermer()`` qui ne renvoie rien."""

    def fermer(self) -> None: ...


@runtime_checkable
class Source(Fermable, Protocol):
    """Un objet ``Fermable`` qui a aussi un attribut ``nom`` (texte) et une
    méthode ``lire()`` qui renvoie un itérateur de ``Brut``."""

    nom: str

    def lire(self) -> Iterator[Brut]: ...


class ClientHTTP(Protocol):
    """Tout objet qui a une méthode ``get(url)`` qui renvoie le corps de la
    réponse en texte."""

    def get(self, url: str) -> str: ...


def _liste_d_objets(nom: str, contenu: object) -> list[Brut]:
    """Vérifie qu'un JSON décodé est une liste d'objets, et la renvoie."""
    if not isinstance(contenu, list):
        raise SourceInvalide(f"{nom} : une liste d'objets est attendue")
    objets: list[Brut] = []
    for i, element in enumerate(contenu):
        if not isinstance(element, dict):
            raise SourceInvalide(f"{nom} : l'élément {i} n'est pas un objet")
        objets.append(element)
    return objets


# Les quatre sources n'héritent de rien : ne changez pas leur ligne « class ».


class SourceMemoire:
    """Des enregistrements déjà en mémoire (pratique pour les tests)."""

    def __init__(
        self, enregistrements: Iterable[Mapping[str, object]], nom: str = "mémoire"
    ) -> None:
        """Garde une copie de chaque enregistrement. ``fermee`` vaut ``False``."""
        self.nom = nom
        self.fermee = False
        self._enregistrements: list[Brut] = [dict(e) for e in enregistrements]

    def lire(self) -> Iterator[Brut]:
        """Une nouvelle copie de chaque enregistrement à chaque lecture."""
        for enregistrement in self._enregistrements:
            yield dict(enregistrement)

    def fermer(self) -> None:
        """Met ``fermee`` à ``True``."""
        self.fermee = True


class SourceCSV:
    """Un fichier CSV avec une ligne d'en-tête, lu paresseusement. Son ``nom``
    est le chemin, tel que reçu, converti en texte."""

    def __init__(self, chemin: str | Path) -> None:
        self.chemin = chemin
        self.nom = str(chemin)
        self._fichier: IO[str] | None = None

    def lire(self) -> Iterator[Brut]:
        """Ouvre le fichier au premier ``next`` (``open`` avec ``newline=""``
        et ``encoding="utf-8"``) ; chaque ligne devient un ``dict``."""
        # Pas de with : c'est fermer() qui ferme le fichier, pas l'abandon du
        # générateur (sinon un simple next(source.lire()) le refermerait aussitôt).
        self._fichier = open(self.chemin, newline="", encoding="utf-8")  # noqa: SIM115
        for ligne in csv.DictReader(self._fichier):
            brut: Brut = dict(ligne)
            yield brut
        self._fichier.close()

    def fermer(self) -> None:
        """Ferme le fichier s'il a été ouvert."""
        if self._fichier is not None:
            self._fichier.close()


class SourceJSON:
    """Un fichier JSON qui contient une liste d'objets. Son ``nom`` est le
    chemin, converti en texte."""

    def __init__(self, chemin: str | Path) -> None:
        self.chemin = chemin
        self.nom = str(chemin)

    def lire(self) -> Iterator[Brut]:
        """Lit tout le fichier (``encoding="utf-8"``), le referme aussitôt, puis
        produit les objets. Lève ``SourceInvalide`` si le contenu n'est pas une
        liste d'objets."""
        with open(self.chemin, encoding="utf-8") as fichier:
            contenu: object = json.load(fichier)
        yield from _liste_d_objets(self.nom, contenu)

    def fermer(self) -> None:
        """Rien à fermer : ``lire`` ferme le fichier aussitôt lu."""


class SourceAPI:
    """Une liste d'objets JSON renvoyée par un service web. Le client HTTP est
    injecté : n'importe quel objet conforme à ``ClientHTTP``. Son ``nom`` est
    l'URL."""

    def __init__(self, client: ClientHTTP, url: str) -> None:
        self.client = client
        self.url = url
        self.nom = url

    def lire(self) -> Iterator[Brut]:
        """N'appelle ``client.get(url)`` qu'au premier ``next``. Lève
        ``SourceInvalide`` si la réponse n'est pas une liste d'objets."""
        contenu: object = json.loads(self.client.get(self.url))
        yield from _liste_d_objets(self.nom, contenu)

    def fermer(self) -> None:
        """Rien à fermer : le client appartient à l'appelant."""


def lire_tout(source: Source) -> list[Brut]:
    """Lit tous les enregistrements, puis ferme la source, même en cas d'erreur."""
    try:
        return list(source.lire())
    finally:
        source.fermer()


def fermer_tout(objets: Iterable[Fermable]) -> int:
    """Ferme chaque objet et renvoie le nombre d'objets fermés."""
    nombre = 0
    for objet in objets:
        objet.fermer()
        nombre += 1
    return nombre

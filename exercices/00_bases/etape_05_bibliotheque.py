"""Étape 5 : classes, attributs, méthodes, héritage et polymorphisme."""


class Livre:
    """Un livre papier, avec les attributs d'instance ``titre``, ``auteur`` et
    ``annee``."""

    def __init__(self, titre: str, auteur: str, annee: int) -> None:
        self.titre = titre
        self.auteur = auteur
        self.annee = annee

    def __repr__(self) -> str:
        """Renvoie ``Livre('Dune', 'Frank Herbert', 1965)``."""
        return f"Livre({self.titre!r}, {self.auteur!r}, {self.annee!r})"

    def description(self) -> str:
        """Renvoie ``"Titre, Auteur (annee)"``."""
        return f"{self.titre}, {self.auteur} ({self.annee})"

    def age(self, annee_courante: int) -> int:
        """Renvoie le nombre d'années écoulées depuis la parution."""
        return annee_courante - self.annee


class LivreNumerique(Livre):
    """Un livre numérique : un livre avec un attribut ``extension`` en plus
    (``"epub"``, ``"pdf"``…)."""

    def __init__(self, titre: str, auteur: str, annee: int, extension: str) -> None:
        super().__init__(titre, auteur, annee)
        self.extension = extension

    def __repr__(self) -> str:
        """Renvoie ``LivreNumerique('Dune', 'Frank Herbert', 1965, 'epub')``."""
        return (
            f"LivreNumerique({self.titre!r}, {self.auteur!r}, "
            f"{self.annee!r}, {self.extension!r})"
        )

    def description(self) -> str:
        """Renvoie la description d'un livre suivie de ``" [extension]"``."""
        return super().description() + f" [{self.extension}]"

    # Pas de méthode age : elle est héritée de Livre.


class Bibliotheque:
    """Une collection de livres, rangés dans l'attribut d'instance ``livres``
    (une liste, vide au départ)."""

    def __init__(self) -> None:
        self.livres: list[Livre] = []

    def ajouter(self, livre: Livre) -> None:
        """Ajoute ``livre`` à la fin de la collection."""
        self.livres.append(livre)

    def par_auteur(self, auteur: str) -> list[Livre]:
        """Renvoie les livres de ``auteur``, dans l'ordre d'ajout."""
        return [livre for livre in self.livres if livre.auteur == auteur]

    def plus_recents(self, n: int = 3) -> list[Livre]:
        """Renvoie les ``n`` livres les plus récents, du plus récent au plus
        ancien. À année égale, l'ordre d'ajout est conservé."""
        tries = sorted(self.livres, key=lambda livre: livre.annee, reverse=True)
        return tries[:n]

    def descriptions(self) -> list[str]:
        """Renvoie la description de chaque livre, dans l'ordre d'ajout."""
        return [livre.description() for livre in self.livres]

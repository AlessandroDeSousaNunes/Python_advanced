"""Étape 1 : annoter un module existant.

Ce carnet de notes fonctionne à peu près, mais il n'a aucune annotation.

1. Annotez-le jusqu'à ce que ``mypy --strict`` passe :

       uv run mypy exercices/05_typage/etape_01_annotations.py

2. Corrigez les trois bugs que mypy révèle en chemin (cherchez les valeurs qui
   peuvent être ``None``). Les docstrings décrivent le comportement attendu.

Interdits : ``Any``, ``cast`` et ``# type: ignore``. On corrige le typage, on
ne fait pas taire mypy.
"""

from collections.abc import Callable, Iterable, Mapping, Sequence

SEUILS: list[tuple[int, str]] = [
    (16, "très bien"),
    (14, "bien"),
    (12, "assez bien"),
    (10, "passable"),
]

COEFFICIENTS: dict[str, float] = {"maths": 3.0, "physique": 2.0, "français": 2.0}


def moyenne(notes: Sequence[float]) -> float | None:
    """Moyenne des notes, ou ``None`` si la liste est vide."""
    if not notes:
        return None
    return sum(notes) / len(notes)


def mention(moyenne_generale: float) -> str:
    """La mention qui correspond à une moyenne."""
    for seuil, nom in SEUILS:
        if moyenne_generale >= seuil:
            return nom
    return "insuffisant"


def lire_note(texte: str) -> float:
    """Convertit ``" 12,5 "`` en ``12.5``."""
    return float(texte.strip().replace(",", "."))


def moyenne_ponderee(
    notes_par_matiere: Mapping[str, float],
    coefficients: Mapping[str, float] = COEFFICIENTS,
) -> float | None:
    """Moyenne pondérée par les coefficients ; une matière sans coefficient
    compte pour 1. ``None`` s'il n'y a aucune note."""
    total = 0.0
    poids = 0.0
    for matiere, note in notes_par_matiere.items():
        # Bug 1 : get(matiere) renvoyait None pour une matière inconnue.
        coefficient = coefficients.get(matiere, 1.0)
        total += note * coefficient
        poids += coefficient
    return total / poids if poids else None


def appliquer(
    notes: Iterable[float], transformation: Callable[[float], float]
) -> list[float]:
    """Applique ``transformation`` à chaque note."""
    return [transformation(note) for note in notes]


def bonus(points: float) -> Callable[[float], float]:
    """Renvoie une fonction qui ajoute ``points`` à une note, sans dépasser 20."""

    def ajouter(note: float) -> float:
        return min(note + points, 20)

    return ajouter


class Eleve:
    def __init__(self, nom: str, notes: Iterable[float] | None = None) -> None:
        self.nom = nom
        self.notes: list[float] = list(notes) if notes is not None else []

    def ajouter(self, note: float) -> None:
        if not 0 <= note <= 20:
            raise ValueError(f"Note hors de [0, 20] : {note}")
        self.notes.append(note)

    def moyenne(self) -> float | None:
        return moyenne(self.notes)


class Classe:
    def __init__(self, nom: str) -> None:
        self.nom = nom
        self.eleves: dict[str, Eleve] = {}

    def inscrire(self, eleve: Eleve) -> None:
        self.eleves[eleve.nom] = eleve

    def chercher(self, nom: str) -> Eleve | None:
        return self.eleves.get(nom)

    def bulletin(self, nom: str) -> str:
        """``"Ada : 15.50 (bien)"``, ``"Ada : aucune note"`` ou
        ``"Ada : inconnu"``."""
        eleve = self.chercher(nom)
        # Bug 2 : l'élève peut être inconnu (chercher renvoie None).
        if eleve is None:
            return f"{nom} : inconnu"
        m = eleve.moyenne()
        # Bug 3 : un élève sans note n'a pas de moyenne.
        if m is None:
            return f"{eleve.nom} : aucune note"
        return f"{eleve.nom} : {m:.2f} ({mention(m)})"

    def classement(self) -> list[tuple[str, float]]:
        """Les élèves qui ont au moins une note, du meilleur au moins bon."""
        moyennes: list[tuple[str, float]] = []
        for eleve in self.eleves.values():
            m = eleve.moyenne()
            if m is not None:
                moyennes.append((eleve.nom, m))
        return sorted(moyennes, key=lambda paire: paire[1], reverse=True)

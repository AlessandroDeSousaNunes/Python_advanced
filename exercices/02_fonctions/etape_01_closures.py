"""Étape 1 : fonctions de première classe et closures."""

from collections.abc import Callable

# --- Des fonctions dans un dictionnaire ---------------------------------------

OPERATIONS: dict[str, Callable[[float, float], float]] = {
    "plus": lambda a, b: a + b,
    "moins": lambda a, b: a - b,
    "fois": lambda a, b: a * b,
    "divise": lambda a, b: a / b,
}


def calculer(nom: str, a: float, b: float) -> float:
    """Applique l'opération ``nom`` de ``OPERATIONS`` à ``a`` et ``b``.

    Lève ``ValueError`` (« opération inconnue ») si ``nom`` n'existe pas.
    """
    if nom not in OPERATIONS:
        raise ValueError(f"opération inconnue : {nom}")
    operation = OPERATIONS[nom]
    return operation(a, b)


# --- Fonctions d'ordre supérieur ----------------------------------------------


def appliquer_n_fois(fn: Callable[[int], int], n: int, x: int) -> int:
    """Renvoie ``fn(fn(...fn(x)))``, avec ``n`` appels. ``n == 0`` renvoie ``x``.

    Lève ``ValueError`` si ``n`` est négatif.
    """
    if n < 0:
        raise ValueError("n doit être positif ou nul")
    for _ in range(n):
        x = fn(x)
    return x


def puissance(exposant: int) -> Callable[[float], float]:
    """Renvoie la fonction qui élève son argument à la puissance ``exposant``."""

    def eleve(x: float) -> float:
        return x**exposant

    return eleve


# --- Closures et état ---------------------------------------------------------


def creer_compteur(depart: int = 0, pas: int = 1) -> Callable[[], int]:
    """Renvoie une fonction qui, à chaque appel, avance de ``pas`` et renvoie la
    nouvelle valeur. Le premier appel renvoie ``depart + pas``."""
    valeur = depart

    def compteur() -> int:
        nonlocal valeur
        valeur += pas
        return valeur

    return compteur


def creer_pile() -> tuple[Callable[[int], None], Callable[[], int], Callable[[], int]]:
    """Renvoie trois fonctions qui partagent la même pile : ``empiler(x)``,
    ``depiler()`` (lève ``IndexError`` si la pile est vide) et ``taille()``."""
    # Pas besoin de nonlocal : on modifie la liste, on ne la réaffecte jamais.
    pile: list[int] = []

    def empiler(x: int) -> None:
        pile.append(x)

    def depiler() -> int:
        if not pile:
            raise IndexError("la pile est vide")
        return pile.pop()

    def taille() -> int:
        return len(pile)

    return empiler, depiler, taille


# --- Le piège de la liaison tardive -------------------------------------------


def multiplicateurs_errone(n: int) -> list[Callable[[int], int]]:
    """Fourni : la version piégée. Toutes les fonctions multiplient par ``n - 1``."""
    return [lambda x: i * x for i in range(n)]  # noqa: B023 (le piège, voulu)


def multiplicateurs(n: int) -> list[Callable[[int], int]]:
    """Renvoie ``n`` fonctions : la i-ème multiplie son argument par ``i``."""
    # i=i fige la valeur de i au moment où chaque lambda est créée.
    return [lambda x, i=i: i * x for i in range(n)]

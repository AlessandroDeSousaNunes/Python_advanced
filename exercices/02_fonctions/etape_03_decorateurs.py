"""Étape 3 : décorateurs simples et ``functools.wraps``.

Les signatures sont typées pour mypy avec ``[**P, R]`` : voir l'encadré
« Typer un décorateur » du README. Dans chaque décorateur, la fonction interne
s'écrit :

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        ...
"""

import time
from collections.abc import Callable, Hashable
from functools import wraps


def trace[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """Affiche chaque appel de ``fn`` et son résultat.

    >>> @trace
    ... def addition(a, b, c=0):
    ...     return a + b + c
    >>> addition(1, 2, c=3)
    -> addition(1, 2, c=3)
    <- addition = 6
    6

    Si ``fn`` lève une exception, affiche ``!! addition a levé ValueError`` et
    laisse passer l'exception.
    """

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        morceaux = [repr(a) for a in args]
        morceaux += [f"{cle}={valeur!r}" for cle, valeur in kwargs.items()]
        print(f"-> {fn.__name__}({', '.join(morceaux)})")
        try:
            resultat = fn(*args, **kwargs)
        except Exception as erreur:
            print(f"!! {fn.__name__} a levé {type(erreur).__name__}")
            raise
        print(f"<- {fn.__name__} = {resultat!r}")
        return resultat

    return wrapper


def chrono[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """Mesure la durée de chaque appel avec ``time.perf_counter`` et affiche
    ``nom : 0.0521s`` (quatre décimales), même si ``fn`` lève une exception."""

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        debut = time.perf_counter()
        try:
            return fn(*args, **kwargs)
        finally:
            duree = time.perf_counter() - debut
            print(f"{fn.__name__} : {duree:.4f}s")

    return wrapper


def memoiser[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """Garde en mémoire le résultat de chaque appel : un second appel avec les
    mêmes arguments renvoie le résultat mémorisé sans rappeler ``fn``. Chaque
    fonction décorée a son propre cache."""
    cache: dict[Hashable, R] = {}

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        cle = (args, tuple(sorted(kwargs.items())))
        if cle not in cache:
            cache[cle] = fn(*args, **kwargs)
        return cache[cle]

    return wrapper

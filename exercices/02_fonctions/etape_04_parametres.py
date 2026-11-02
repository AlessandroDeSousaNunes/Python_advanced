"""Étape 4 : décorateurs paramétrés.

Un décorateur paramétré a trois niveaux : la fabrique (qui reçoit les
paramètres), le décorateur (qui reçoit la fonction) et le wrapper (qui reçoit
les arguments de chaque appel). Les signatures des fabriques sont données.
"""

import time
from collections.abc import Callable
from functools import wraps


def repeter[**P, R](n: int) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """``@repeter(3)`` appelle la fonction trois fois et renvoie le dernier
    résultat. Lève ``ValueError`` dès ``repeter(0)`` si ``n < 1``."""
    if n < 1:
        raise ValueError("n doit valoir au moins 1")

    def decorateur(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for _ in range(n - 1):
                fn(*args, **kwargs)
            return fn(*args, **kwargs)

        return wrapper

    return decorateur


def reessayer[**P, R](
    tentatives: int,
    *,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    delai: float = 0.0,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Appelle la fonction jusqu'à ``tentatives`` fois tant qu'elle lève une
    des ``exceptions``.

    - entre deux tentatives, attend ``delai`` secondes avec ``time.sleep`` ;
    - après la dernière tentative ratée, l'exception remonte ;
    - une exception qui n'est pas dans ``exceptions`` remonte immédiatement.

    Lève ``ValueError`` dès l'appel de ``reessayer`` si ``tentatives < 1``.
    """
    if tentatives < 1:
        raise ValueError("il faut au moins une tentative")

    def decorateur(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            for numero in range(1, tentatives + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions:
                    if numero == tentatives:
                        raise
                    time.sleep(delai)
            raise AssertionError("inatteignable")

        return wrapper

    return decorateur


def limiter_appels[**P, R](
    maximum: int,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Autorise au plus ``maximum`` appels de la fonction décorée. Au-delà,
    lève ``RuntimeError`` sans appeler la fonction.

    Chaque fonction décorée a son propre compteur, même si plusieurs fonctions
    sont décorées par le même ``limiter_appels(2)``.
    """

    def decorateur(fn: Callable[P, R]) -> Callable[P, R]:
        # Le compteur est créé ici : un par fonction décorée.
        appels = 0

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            nonlocal appels
            if appels >= maximum:
                raise RuntimeError(f"{fn.__name__} : plus de {maximum} appels")
            appels += 1
            return fn(*args, **kwargs)

        return wrapper

    return decorateur


def enregistrer_dans[F: Callable[..., object]](
    registre: dict[str, Callable[..., object]], nom: str | None = None
) -> Callable[[F], F]:
    """Enregistre la fonction décorée dans ``registre``, sous ``nom`` ou, à
    défaut, sous son propre nom, puis la renvoie **telle quelle**.

    Lève ``ValueError`` si le nom est déjà pris (le registre n'est pas modifié).
    """

    def decorateur(fn: F) -> F:
        cle = nom if nom is not None else fn.__name__  # type: ignore[attr-defined]
        if cle in registre:
            raise ValueError(f"nom déjà pris : {cle}")
        registre[cle] = fn
        return fn

    return decorateur

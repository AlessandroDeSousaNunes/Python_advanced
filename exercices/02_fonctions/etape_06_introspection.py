"""Étape 6 : décorateurs de classe et annotations."""

import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any


def ajouter_repr[T](cls: type[T]) -> type[T]:
    """Ajoute à ``cls`` un ``__repr__`` construit à partir des attributs
    d'instance : ``Point(x=1, y=2)``. Le nom affiché est celui de la classe
    réelle de l'objet (une sous-classe affiche son propre nom). Renvoie la même
    classe, modifiée."""

    def __repr__(self: object) -> str:
        attributs = ", ".join(f"{nom}={valeur!r}" for nom, valeur in vars(self).items())
        return f"{type(self).__name__}({attributs})"

    setattr(cls, "__repr__", __repr__)  # noqa: B010
    return cls


def verifier_types[**P, R](fn: Callable[P, R]) -> Callable[P, R]:
    """Vérifie à chaque appel les arguments et la valeur de retour de ``fn``
    dont l'annotation est une **classe** (``int``, ``str``, ``Utilisateur``…).

    - les autres annotations (``list[int]``, ``int | None``, ``None``…) et les
      paramètres sans annotation sont ignorés, comme ``*args`` et ``**kwargs`` ;
    - un argument du mauvais type lève ``TypeError`` avant l'appel, avec le nom
      du paramètre dans le message ;
    - un résultat du mauvais type lève ``TypeError`` après l'appel.
    """
    signature = inspect.signature(fn)
    vide = inspect.Parameter.empty  # « pas d'annotation » : c'est aussi une classe

    # On lit les annotations une seule fois, au moment de la décoration.
    a_verifier = {}
    for nom, parametre in signature.parameters.items():
        if parametre.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        annotation = parametre.annotation
        if isinstance(annotation, type) and annotation is not vide:
            a_verifier[nom] = annotation
    retour = signature.return_annotation
    type_retour = retour if isinstance(retour, type) and retour is not vide else None

    @wraps(fn)
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        arguments = signature.bind(*args, **kwargs).arguments
        for nom, attendu in a_verifier.items():
            if nom in arguments and not isinstance(arguments[nom], attendu):
                raise TypeError(
                    f"{nom} doit être de type {attendu.__name__}, "
                    f"pas {type(arguments[nom]).__name__}"
                )
        resultat = fn(*args, **kwargs)
        if type_retour is not None and not isinstance(resultat, type_retour):
            raise TypeError(
                f"le résultat doit être de type {type_retour.__name__}, "
                f"pas {type(resultat).__name__}"
            )
        return resultat

    return wrapper


def decorer_methodes[T](
    decorateur: Callable[[Callable[..., Any]], Callable[..., Any]],
) -> Callable[[type[T]], type[T]]:
    """Décorateur de classe paramétré : applique ``decorateur`` à chaque méthode
    **publique** (nom sans ``_`` initial) définie dans le corps de la classe.
    Les méthodes héritées ne sont pas touchées. Renvoie la même classe."""

    def decorer(cls: type[T]) -> type[T]:
        # vars(cls) ne contient que ce qui est écrit dans le corps de la classe.
        for nom, valeur in list(vars(cls).items()):
            if not nom.startswith("_") and inspect.isfunction(valeur):
                setattr(cls, nom, decorateur(valeur))
        return cls

    return decorer

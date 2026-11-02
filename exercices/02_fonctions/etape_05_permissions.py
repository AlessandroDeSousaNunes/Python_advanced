"""Étape 5 : un décorateur de permissions, et l'ordre d'empilement."""

import inspect
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps


@dataclass(frozen=True)
class Utilisateur:
    """Fourni : un utilisateur et l'ensemble de ses permissions."""

    nom: str
    permissions: frozenset[str] = frozenset()


def requiert_permission[**P, R](
    *permissions: str,
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """``@requiert_permission("admin", "audit")`` n'autorise l'appel que si
    l'argument ``utilisateur`` possède **toutes** ces permissions.

    - ``requiert_permission()`` sans permission lève ``ValueError`` ;
    - décorer une fonction sans paramètre ``utilisateur`` lève ``TypeError`` ;
    - ``utilisateur`` peut être passé par position ou par nom ;
    - s'il manque, ou s'il n'est pas un ``Utilisateur``, l'appel lève
      ``PermissionError`` ;
    - s'il lui manque des permissions, l'appel lève ``PermissionError`` dont le
      message cite chacune d'elles. La fonction n'est pas appelée.
    """
    if not permissions:
        raise ValueError("il faut au moins une permission")

    def decorateur(fn: Callable[P, R]) -> Callable[P, R]:
        signature = inspect.signature(fn)
        parametre = signature.parameters.get("utilisateur")
        if parametre is None or parametre.kind == inspect.Parameter.VAR_KEYWORD:
            raise TypeError(f"{fn.__name__} n'a pas de paramètre utilisateur")

        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            arguments = signature.bind_partial(*args, **kwargs).arguments
            utilisateur = arguments.get("utilisateur")
            if not isinstance(utilisateur, Utilisateur):
                raise PermissionError("aucun utilisateur valide")
            manquantes = [p for p in permissions if p not in utilisateur.permissions]
            if manquantes:
                raise PermissionError(
                    f"permissions manquantes : {', '.join(manquantes)}"
                )
            return fn(*args, **kwargs)

        return wrapper

    return decorateur


def journaliser[**P, R](
    journal: list[str],
) -> Callable[[Callable[P, R]], Callable[P, R]]:
    """Ajoute le nom de la fonction à ``journal`` **avant** chaque appel."""

    def decorateur(fn: Callable[P, R]) -> Callable[P, R]:
        @wraps(fn)
        def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            journal.append(fn.__name__)
            return fn(*args, **kwargs)

        return wrapper

    return decorateur


# --- Empilement ---------------------------------------------------------------

JOURNAL: list[str] = []


# journaliser au-dessus : il s'exécute en premier, donc même un appel refusé
# est noté.
@journaliser(JOURNAL)
@requiert_permission("admin")
def supprimer_compte(utilisateur: Utilisateur, numero: str) -> str:
    """Réservé à "admin". Tout appel est journalisé, même refusé."""
    return f"compte {numero} supprimé"


# requiert_permission au-dessus : un appel refusé s'arrête avant le journal.
@requiert_permission("lecture")
@journaliser(JOURNAL)
def consulter_compte(utilisateur: Utilisateur, numero: str) -> str:
    """Réservé à "lecture". Seuls les appels autorisés sont journalisés."""
    return f"compte {numero}"


@journaliser(JOURNAL)
@requiert_permission("lecture", "ecriture")
def renommer_compte(utilisateur: Utilisateur, numero: str, *, titulaire: str) -> str:
    """Réservé à qui a "lecture" et "ecriture". Tout appel est journalisé."""
    return f"compte {numero} : {titulaire}"

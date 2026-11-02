"""Étape 2 : ``*args``, ``**kwargs``, arguments nommés obligatoires et
dépaquetage."""

import inspect
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Any


@dataclass
class Profil:
    """Fourni : le profil renvoyé par ``creer_profil``."""

    nom: str
    role: str
    actif: bool
    infos: dict[str, str]


def creer_profil(
    nom: str, role: str = "invite", *, actif: bool = True, **infos: str
) -> Profil:
    """Crée un profil. ``actif`` ne peut être passé que par son nom, et les
    autres arguments nommés sont rangés dans ``infos``."""
    return Profil(nom, role, actif, infos)


def ligne_de_journal(
    niveau: str, message: str, *details: object, sep: str = " | ", **contexte: object
) -> str:
    """Construit une ligne de journal.

    >>> ligne_de_journal("info", "Démarrage", "v1.2", 3, utilisateur="alice")
    '[INFO] Démarrage | v1.2 | 3 (utilisateur=alice)'
    """
    morceaux = [message] + [str(detail) for detail in details]
    ligne = f"[{niveau.upper()}] " + sep.join(morceaux)
    if contexte:
        paires = [f"{cle}={valeur}" for cle, valeur in contexte.items()]
        ligne += " (" + ", ".join(paires) + ")"
    return ligne


def appliquer_lot[R](
    fn: Callable[..., R], lots: Iterable[tuple[Any, ...]], **options: Any
) -> list[R]:
    """Appelle ``fn`` une fois par tuple de ``lots`` : les éléments du tuple
    deviennent les arguments positionnels, et ``options`` les arguments nommés
    de chaque appel."""
    return [fn(*lot, **options) for lot in lots]


def appeler_ou_defaut[R](
    fn: Callable[..., R], *args: Any, defaut: R | None = None, **kwargs: Any
) -> R | None:
    """Appelle ``fn(*args, **kwargs)`` et renvoie son résultat. Si l'appel lève
    une ``Exception``, renvoie ``defaut``. ``defaut`` n'est jamais transmis à
    ``fn``."""
    try:
        return fn(*args, **kwargs)
    except Exception:
        return defaut


# --- Inspecter une signature --------------------------------------------------


def classer_parametres(fn: Callable[..., object]) -> dict[str, list[str]]:
    """Range les noms des paramètres de ``fn`` en quatre catégories, toujours
    présentes : ``"positionnels"``, ``"args"``, ``"nommes"`` et ``"kwargs"``."""
    classes: dict[str, list[str]] = {
        "positionnels": [],
        "args": [],
        "nommes": [],
        "kwargs": [],
    }
    for nom, parametre in inspect.signature(fn).parameters.items():
        if parametre.kind == inspect.Parameter.VAR_POSITIONAL:
            classes["args"].append(nom)
        elif parametre.kind == inspect.Parameter.KEYWORD_ONLY:
            classes["nommes"].append(nom)
        elif parametre.kind == inspect.Parameter.VAR_KEYWORD:
            classes["kwargs"].append(nom)
        else:
            classes["positionnels"].append(nom)
    return classes


def parametres_obligatoires(fn: Callable[..., object]) -> list[str]:
    """Renvoie, dans l'ordre, les paramètres qu'un appel doit obligatoirement
    fournir : ni valeur par défaut, ni ``*args``, ni ``**kwargs``."""
    obligatoires = []
    for nom, parametre in inspect.signature(fn).parameters.items():
        if parametre.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        if parametre.default is inspect.Parameter.empty:
            obligatoires.append(nom)
    return obligatoires

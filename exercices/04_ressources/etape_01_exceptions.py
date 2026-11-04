"""Étape 1 : une hiérarchie d'exceptions métier.

Exception
└── ErreurBanque
    ├── MontantInvalide   (aussi un ValueError)
    ├── SoldeInsuffisant
    └── CompteFerme
"""

import math
from collections.abc import Callable
from dataclasses import dataclass


def _nombre(x: float) -> str:
    """Affiche ``70`` plutôt que ``70.0`` quand le nombre est entier."""
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)


class ErreurBanque(Exception):
    """Base de toutes les erreurs bancaires."""


class MontantInvalide(ErreurBanque, ValueError):
    """Montant nul, négatif ou non fini."""

    def __init__(self, montant: float) -> None:
        self.montant = montant
        super().__init__(f"Montant invalide : {_nombre(montant)}")


class SoldeInsuffisant(ErreurBanque):
    """Retrait supérieur au solde."""

    def __init__(self, solde: float, montant: float) -> None:
        self.solde = solde
        self.montant = montant
        super().__init__(
            f"Retrait de {_nombre(montant)} refusé (solde : {_nombre(solde)})"
        )

    @property
    def manque(self) -> float:
        """Ce qu'il faudrait ajouter au solde pour que le retrait passe."""
        return self.montant - self.solde


class CompteFerme(ErreurBanque):
    """Opération sur un compte fermé."""

    def __init__(self, numero: str) -> None:
        self.numero = numero
        super().__init__(f"Le compte {numero} est fermé")


@dataclass
class Compte:
    """Un compte minimal. Fourni."""

    numero: str
    solde: float = 0.0
    ouvert: bool = True


def retirer(compte: Compte, montant: float) -> float:
    """Retire ``montant`` du compte et renvoie le nouveau solde.

    Vérifie, dans cet ordre : que le compte est ouvert (``CompteFerme``), que
    le montant est strictement positif et fini (``MontantInvalide``), puis
    qu'il ne dépasse pas le solde (``SoldeInsuffisant``). En cas d'erreur, le
    solde n'est pas modifié."""
    if not compte.ouvert:
        raise CompteFerme(compte.numero)
    if not math.isfinite(montant) or montant <= 0:
        raise MontantInvalide(montant)
    if montant > compte.solde:
        raise SoldeInsuffisant(compte.solde, montant)
    compte.solde -= montant
    return compte.solde


def tenter_retrait(compte: Compte, montant: float) -> str:
    """Appelle ``retirer`` et décrit le résultat par une phrase :

    - ``"ok : nouveau solde 70"`` si le retrait passe ;
    - ``"refusé : il manque 30"`` pour un solde insuffisant ;
    - ``"erreur bancaire : <message>"`` pour toute autre ``ErreurBanque``.

    Les autres exceptions se propagent."""
    # Du plus précis au plus général : SoldeInsuffisant est aussi une ErreurBanque.
    try:
        solde = retirer(compte, montant)
    except SoldeInsuffisant as e:
        return f"refusé : il manque {_nombre(e.manque)}"
    except ErreurBanque as e:
        return f"erreur bancaire : {e}"
    return f"ok : nouveau solde {_nombre(solde)}"


def appeler_prudemment[T](
    fonction: Callable[[], T],
    defaut: T,
    erreurs: list[Exception] | None = None,
) -> T:
    """Appelle ``fonction()`` et renvoie son résultat. Si elle lève une
    exception applicative (une ``Exception``), renvoie ``defaut`` et ajoute
    l'exception à ``erreurs`` si la liste est fournie. ``KeyboardInterrupt``
    et ``SystemExit`` ne sont jamais rattrapées."""
    # KeyboardInterrupt et SystemExit héritent de BaseException, pas d'Exception.
    try:
        return fonction()
    except Exception as e:
        if erreurs is not None:
            erreurs.append(e)
        return defaut


def lire_montant(champs: dict[str, str], cle: str) -> float | None:
    """Renvoie la valeur de ``champs[cle]`` convertie en ``float`` (la virgule
    décimale est acceptée : ``"12,5"``), ou ``None`` si la clé est absente ou
    si la valeur n'est pas un nombre. Style EAFP : on essaie, puis on rattrape
    exactement ``KeyError`` et ``ValueError``."""
    try:
        return float(champs[cle].replace(",", "."))
    except (KeyError, ValueError):
        return None

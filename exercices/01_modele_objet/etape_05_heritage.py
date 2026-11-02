"""Étape 5 : héritage, ``super()``, mixin et MRO."""

from abc import ABC, abstractmethod
from typing import Any


class Compte(ABC):
    """Un compte bancaire abstrait : chaque sorte de compte fixe ses frais.

    Attribut de classe ``decouvert_autorise`` : ``0.0`` (pas de découvert).
    """

    decouvert_autorise = 0.0

    def __init__(self, titulaire: str, solde: float = 0.0) -> None:
        self.titulaire = titulaire
        self.solde = solde

    @abstractmethod
    def frais(self, montant: float) -> float:
        """Frais prélevés en plus d'un retrait de ``montant``."""

    def deposer(self, montant: float) -> None:
        """Lève ``ValueError`` si ``montant`` n'est pas strictement positif."""
        if montant <= 0:
            raise ValueError("le montant doit être strictement positif")
        self.solde += montant

    def retirer(self, montant: float) -> None:
        """Retire ``montant`` plus les frais. Lève ``ValueError`` si ``montant``
        n'est pas strictement positif, ou (« solde insuffisant ») si le solde
        passerait sous ``-decouvert_autorise``."""
        if montant <= 0:
            raise ValueError("le montant doit être strictement positif")
        total = montant + self.frais(montant)
        if self.solde - total < -self.decouvert_autorise:
            raise ValueError("solde insuffisant")
        self.solde -= total


class CompteCourant(Compte):
    """Sans frais, avec un découvert autorisé de 100 €."""

    decouvert_autorise = 100.0

    def frais(self, montant: float) -> float:
        return 0.0


class CompteEpargne(Compte):
    """Rémunéré au taux ``taux`` ; chaque retrait coûte 1 % du montant, arrondi
    au centime. Pas de découvert."""

    def __init__(self, titulaire: str, solde: float = 0.0, taux: float = 0.02) -> None:
        super().__init__(titulaire, solde)
        self.taux = taux

    def frais(self, montant: float) -> float:
        return round(montant * 0.01, 2)

    def appliquer_interets(self) -> float:
        """Ajoute au solde les intérêts (``solde * taux``, arrondis au centime)
        et les renvoie."""
        interets = round(self.solde * self.taux, 2)
        self.solde += interets
        return interets


class Historisable(Compte):
    """Mixin : garde la trace des dépôts et des retraits réussis, sous la forme
    ``"dépôt de 50.00"`` et ``"retrait de 20.00"``.

    Il ne s'instancie pas seul (``frais`` reste abstraite) : on le combine avec
    une sorte de compte concrète.
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Transmet tous les arguments à la classe suivante dans le MRO, puis
        crée l'historique."""
        super().__init__(*args, **kwargs)
        self._historique: list[str] = []

    @property
    def historique(self) -> list[str]:
        """Une copie de l'historique."""
        return list(self._historique)

    def deposer(self, montant: float) -> None:
        super().deposer(montant)
        self._historique.append(f"dépôt de {montant:.2f}")

    def retirer(self, montant: float) -> None:
        super().retirer(montant)
        self._historique.append(f"retrait de {montant:.2f}")


# Le mixin vient en premier : ses deposer et retirer passent avant ceux du compte.
class CompteCourantHistorise(Historisable, CompteCourant):
    pass


class CompteEpargneHistorise(Historisable, CompteEpargne):
    pass

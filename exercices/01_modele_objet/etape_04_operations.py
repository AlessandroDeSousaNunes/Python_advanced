"""Étape 4 : classe abstraite ``Operation`` et objets appelables."""

from abc import ABC, abstractmethod


class Compte:
    """Un compte minimal, fourni : il garde les opérations réussies dans
    ``historique``."""

    def __init__(self, titulaire: str, solde: float = 0.0) -> None:
        self.titulaire = titulaire
        self.solde = solde
        self.historique: list[Operation] = []


class Operation(ABC):
    """Une opération bancaire d'un montant strictement positif.

    Une sous-classe doit fournir ``executer`` et la propriété ``libelle``.
    ``__call__`` et ``__repr__`` sont écrits ici, une fois pour toutes.
    """

    def __init__(self, montant: float) -> None:
        """Lève ``ValueError`` si ``montant`` n'est pas strictement positif."""
        if montant <= 0:
            raise ValueError("le montant doit être strictement positif")
        self.montant = montant

    @abstractmethod
    def executer(self, compte: Compte) -> None:
        """Applique l'opération à ``compte`` (sans toucher à l'historique)."""

    @property
    @abstractmethod
    def libelle(self) -> str:
        """Description lisible de l'opération."""

    def __call__(self, compte: Compte) -> None:
        """Exécute l'opération sur ``compte``, puis l'ajoute à son historique.
        Une opération qui échoue n'est pas historisée."""
        self.executer(compte)
        compte.historique.append(self)

    def __repr__(self) -> str:
        """Renvoie ``Depot(50)``, ``Retrait(20.5)``… selon la classe réelle."""
        return f"{type(self).__name__}({self.montant!r})"


class Depot(Operation):
    """Ajoute le montant au solde. Libellé : ``Dépôt de 50.00 €``."""

    def executer(self, compte: Compte) -> None:
        compte.solde += self.montant

    @property
    def libelle(self) -> str:
        return f"Dépôt de {self.montant:.2f} €"


class Retrait(Operation):
    """Retire le montant du solde. Lève ``ValueError`` (« solde insuffisant »)
    si le solde ne suffit pas. Libellé : ``Retrait de 20.00 €``."""

    def executer(self, compte: Compte) -> None:
        if self.montant > compte.solde:
            raise ValueError("solde insuffisant")
        compte.solde -= self.montant

    @property
    def libelle(self) -> str:
        return f"Retrait de {self.montant:.2f} €"


class Virement(Operation):
    """Retire le montant du compte sur lequel on l'exécute et l'ajoute au compte
    ``destination``. Lève ``ValueError`` (« solde insuffisant ») sans rien
    modifier si le solde ne suffit pas.
    Libellé : ``Virement de 30.00 € vers Bob``."""

    def __init__(self, montant: float, destination: Compte) -> None:
        super().__init__(montant)
        self.destination = destination

    def executer(self, compte: Compte) -> None:
        if self.montant > compte.solde:
            raise ValueError("solde insuffisant")
        compte.solde -= self.montant
        self.destination.solde += self.montant

    @property
    def libelle(self) -> str:
        return f"Virement de {self.montant:.2f} € vers {self.destination.titulaire}"


def releve(compte: Compte) -> list[str]:
    """Renvoie le libellé de chaque opération de l'historique de ``compte``."""
    return [operation.libelle for operation in compte.historique]

"""Étape 6 : dataclasses, ``__post_init__``, ``frozen`` et ``Enum``."""

from dataclasses import dataclass, field
from enum import Enum


class Nature(Enum):
    """La nature d'une transaction : ``DEPOT`` (valeur ``"dépôt"``) ou
    ``RETRAIT`` (valeur ``"retrait"``)."""

    DEPOT = "dépôt"
    RETRAIT = "retrait"


@dataclass(frozen=True)
class Transaction:
    """Une transaction : immuable, comparable par valeur et hachable."""

    nature: Nature
    montant: float

    def __post_init__(self) -> None:
        """Lève ``ValueError`` si ``montant`` n'est pas strictement positif."""
        if self.montant <= 0:
            raise ValueError("le montant doit être strictement positif")

    @property
    def valeur(self) -> float:
        """Le montant signé : positif pour un dépôt, négatif pour un retrait."""
        if self.nature is Nature.DEPOT:
            return self.montant
        return -self.montant


@dataclass
class Compte:
    """Un compte bancaire, égal à un autre s'il a le même numéro.

    - ``solde`` vaut ``0.0`` par défaut, ``transactions`` une liste vide ;
    - seul ``numero`` compte pour ``==`` ;
    - ``transactions`` n'apparaît pas dans le ``repr``.
    """

    numero: str
    titulaire: str = field(compare=False)
    solde: float = field(default=0.0, compare=False)
    transactions: list[Transaction] = field(
        default_factory=list, compare=False, repr=False
    )

    def __post_init__(self) -> None:
        """Retire les espaces autour du titulaire. Lève ``ValueError`` si le
        titulaire est vide ou si le solde est négatif."""
        self.titulaire = self.titulaire.strip()
        if not self.titulaire:
            raise ValueError("le titulaire ne peut pas être vide")
        if self.solde < 0:
            raise ValueError("le solde ne peut pas être négatif")

    def deposer(self, montant: float) -> Transaction:
        """Crée la transaction, l'applique, l'enregistre et la renvoie."""
        transaction = Transaction(Nature.DEPOT, montant)
        self.solde += transaction.valeur
        self.transactions.append(transaction)
        return transaction

    def retirer(self, montant: float) -> Transaction:
        """Comme ``deposer`` ; lève ``ValueError`` (« solde insuffisant ») si le
        solde ne suffit pas, sans rien enregistrer."""
        transaction = Transaction(Nature.RETRAIT, montant)
        if montant > self.solde:
            raise ValueError("solde insuffisant")
        self.solde += transaction.valeur
        self.transactions.append(transaction)
        return transaction


def bilan(transactions: list[Transaction]) -> dict[Nature, float]:
    """Total des montants par nature. Chaque nature est présente, même à 0."""
    totaux = {nature: 0.0 for nature in Nature}
    for transaction in transactions:
        totaux[transaction.nature] += transaction.montant
    return totaux

"""Étape 3 : méthodes spéciales (dunder methods)."""


class Compte:
    """Un compte bancaire identifié par son numéro (``"FR-001"``…).

    ``__init__``, ``deposer`` et ``retirer`` sont fournis : cette étape porte
    uniquement sur les méthodes spéciales.
    """

    def __init__(self, numero: str, titulaire: str, solde: float = 0.0) -> None:
        self.numero = numero
        self.titulaire = titulaire
        self.solde = solde
        self.operations: list[float] = []

    def deposer(self, montant: float) -> None:
        if montant <= 0:
            raise ValueError("le montant doit être strictement positif")
        self.solde += montant
        self.operations.append(montant)

    def retirer(self, montant: float) -> None:
        if montant <= 0:
            raise ValueError("le montant doit être strictement positif")
        if montant > self.solde:
            raise ValueError("solde insuffisant")
        self.solde -= montant
        self.operations.append(-montant)

    # --- Méthodes spéciales ---------------------------------------------------

    def __repr__(self) -> str:
        """Renvoie ``Compte('FR-001', 'Alice', 100.0)``."""
        return f"Compte({self.numero!r}, {self.titulaire!r}, {self.solde!r})"

    def __str__(self) -> str:
        """Renvoie ``Compte FR-001 (Alice) : 100.00 €``."""
        return f"Compte {self.numero} ({self.titulaire}) : {self.solde:.2f} €"

    def __eq__(self, autre: object) -> bool:
        """Deux comptes sont égaux s'ils ont le même numéro."""
        if not isinstance(autre, Compte):
            return NotImplemented
        return self.numero == autre.numero

    def __hash__(self) -> int:
        """Cohérent avec ``__eq__``."""
        return hash(self.numero)

    def __len__(self) -> int:
        """Le nombre d'opérations."""
        return len(self.operations)

    def __bool__(self) -> bool:
        """Vrai si le solde est strictement positif."""
        return self.solde > 0

    def __lt__(self, autre: object) -> bool:
        """Compare les soldes."""
        if not isinstance(autre, Compte):
            return NotImplemented
        return self.solde < autre.solde

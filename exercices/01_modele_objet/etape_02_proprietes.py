"""Étape 2 : propriétés, méthodes de classe et méthodes statiques."""

import math
from typing import Self


class Compte:
    """Un compte bancaire dont le solde ne change que par des opérations.

    Les données sont rangées dans des attributs « privés » (``_titulaire``,
    ``_solde``, ``_operations``) et exposées par des propriétés.
    """

    def __init__(self, titulaire: str, solde: float = 0.0) -> None:
        """Lève ``ValueError`` si ``solde`` est négatif ou si ``titulaire`` est
        vide."""
        if solde < 0:
            raise ValueError("le solde initial ne peut pas être négatif")
        self.titulaire = titulaire
        self._solde = solde
        self._operations: list[float] = []

    # --- Propriétés -----------------------------------------------------------

    @property
    def titulaire(self) -> str:
        """Le nom du titulaire, sans espaces aux extrémités."""
        return self._titulaire

    @titulaire.setter
    def titulaire(self, nom: str) -> None:
        nom = nom.strip()
        if not nom:
            raise ValueError("le titulaire ne peut pas être vide")
        self._titulaire = nom

    @property
    def solde(self) -> float:
        """Le solde, en lecture seule."""
        return self._solde

    @property
    def operations(self) -> tuple[float, ...]:
        """Les montants des opérations, dans un tuple : une copie qu'on ne peut
        pas modifier."""
        return tuple(self._operations)

    @property
    def total_depots(self) -> float:
        """La somme des dépôts (les opérations positives)."""
        return sum(m for m in self._operations if m > 0)

    # --- Méthodes statiques et de classe --------------------------------------

    @staticmethod
    def montant_valide(montant: float) -> bool:
        """Un montant est valide s'il est fini et strictement positif."""
        return math.isfinite(montant) and montant > 0

    @classmethod
    def depuis_ligne(cls, ligne: str) -> Self:
        """Construit un compte depuis ``"Alice ; 150.5"``.

        Lève ``ValueError`` si la ligne n'a pas exactement deux champs, ou si le
        solde n'est pas un nombre. Appelé sur une sous-classe, renvoie une
        instance de cette sous-classe.
        """
        champs = ligne.split(";")
        if len(champs) != 2:
            raise ValueError(f"2 champs attendus : {ligne!r}")
        titulaire, solde = champs
        return cls(titulaire.strip(), float(solde))

    # --- Opérations -----------------------------------------------------------

    def deposer(self, montant: float) -> None:
        """Lève ``ValueError`` si le montant n'est pas valide."""
        if not self.montant_valide(montant):
            raise ValueError(f"montant invalide : {montant}")
        self._solde += montant
        self._operations.append(montant)

    def retirer(self, montant: float) -> None:
        """Lève ``ValueError`` si le montant n'est pas valide, ou s'il dépasse
        le solde (message contenant « insuffisant »)."""
        if not self.montant_valide(montant):
            raise ValueError(f"montant invalide : {montant}")
        if montant > self._solde:
            raise ValueError("solde insuffisant")
        self._solde -= montant
        self._operations.append(-montant)

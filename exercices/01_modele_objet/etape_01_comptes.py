"""Étape 1 : attributs d'instance, attributs de classe et inspection."""


class Compte:
    """Un compte bancaire.

    Attributs de **classe** (partagés par tous les comptes) :

    - ``banque`` : ``"Banque Python"`` ;
    - ``plafond_retrait`` : ``1000.0``, le montant maximal d'un retrait ;
    - ``_prochain_numero`` : ``1``, le numéro que recevra le prochain compte.

    Attributs d'**instance** (un par compte) : ``titulaire``, ``solde``,
    ``numero`` et ``operations`` (la liste des montants, positifs pour un dépôt,
    négatifs pour un retrait).
    """

    banque = "Banque Python"
    plafond_retrait = 1000.0
    _prochain_numero = 1

    def __init__(self, titulaire: str, solde: float = 0.0) -> None:
        """Lève ``ValueError`` si ``solde`` est négatif. Donne au compte le
        numéro ``_prochain_numero``, puis incrémente le compteur de la classe."""
        if solde < 0:
            raise ValueError("le solde initial ne peut pas être négatif")
        self.titulaire = titulaire
        self.solde = solde
        self.numero = Compte._prochain_numero
        Compte._prochain_numero += 1
        self.operations: list[float] = []

    def deposer(self, montant: float) -> None:
        """Ajoute ``montant`` au solde et l'enregistre dans ``operations``.

        Lève ``ValueError`` si ``montant`` n'est pas strictement positif.
        """
        if montant <= 0:
            raise ValueError("le montant doit être strictement positif")
        self.solde += montant
        self.operations.append(montant)

    def retirer(self, montant: float) -> None:
        """Retire ``montant`` du solde et enregistre ``-montant``.

        Lève ``ValueError`` si ``montant`` n'est pas strictement positif, si
        ``montant`` dépasse le plafond (message contenant « plafond ») ou le
        solde (message contenant « insuffisant »).
        """
        if montant <= 0:
            raise ValueError("le montant doit être strictement positif")
        if montant > self.plafond_retrait:
            raise ValueError("montant au-delà du plafond de retrait")
        if montant > self.solde:
            raise ValueError("solde insuffisant")
        self.solde -= montant
        self.operations.append(-montant)


def attributs_d_instance(objet: object) -> list[str]:
    """Renvoie les noms des attributs d'instance de ``objet``, triés."""
    return sorted(vars(objet))

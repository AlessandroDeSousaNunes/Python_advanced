"""Étape 3 : ``TypedDict``, ``Literal`` et ``Callable``.

Des commandes reçues en JSON. Les ``TypedDict`` décrivent leur forme pour
mypy, mais Python ne vérifie rien à l'exécution : ``lire_commande`` valide
donc les données brutes avant de les déclarer ``Commande``.
"""

import math
from collections.abc import Callable, Iterable
from typing import Literal, NotRequired, TypedDict, TypeGuard, get_args

Statut = Literal["en_attente", "payee", "expediee", "livree", "annulee"]


class Article(TypedDict):
    nom: str
    prix: float
    quantite: int


class Commande(TypedDict):
    id: int
    client: str
    statut: Statut
    articles: list[Article]
    remise: NotRequired[float]


class Resume(TypedDict):
    id: int
    client: str
    total: float
    nb_articles: int


TRANSITIONS: dict[Statut, frozenset[Statut]] = {
    "en_attente": frozenset({"payee", "annulee"}),
    "payee": frozenset({"expediee", "annulee"}),
    "expediee": frozenset({"livree"}),
    "livree": frozenset(),
    "annulee": frozenset(),
}


class CommandeInvalide(ValueError):
    """Des données brutes qui ne forment pas une commande valide."""

    def __init__(self, champ: str, message: str) -> None:
        self.champ = champ
        super().__init__(f"{champ} : {message}")


class TransitionInvalide(Exception):
    def __init__(self, ancien: Statut, nouveau: Statut) -> None:
        self.ancien = ancien
        self.nouveau = nouveau
        super().__init__(f"Transition interdite : {ancien} -> {nouveau}")


def total(commande: Commande) -> float:
    """Somme de ``prix * quantite``, moins la remise éventuelle (une fraction
    entre 0 et 1), arrondie à deux décimales."""
    brut = sum(article["prix"] * article["quantite"] for article in commande["articles"])
    remise = commande.get("remise", 0.0)
    return round(brut * (1 - remise), 2)


def resumer(commande: Commande) -> Resume:
    """``nb_articles`` compte les quantités, pas les lignes."""
    return {
        "id": commande["id"],
        "client": commande["client"],
        "total": total(commande),
        "nb_articles": sum(article["quantite"] for article in commande["articles"]),
    }


def est_statut(valeur: object) -> TypeGuard[Statut]:
    """Vrai si ``valeur`` est l'un des statuts de ``Statut``. Pour mypy, une
    valeur qui passe ce test est un ``Statut``."""
    return isinstance(valeur, str) and valeur in get_args(Statut)


def changer_statut(commande: Commande, nouveau: Statut) -> Commande:
    """Renvoie une copie de la commande avec le nouveau statut, si
    ``TRANSITIONS`` l'autorise. Sinon, lève ``TransitionInvalide``."""
    ancien = commande["statut"]
    if nouveau not in TRANSITIONS[ancien]:
        raise TransitionInvalide(ancien, nouveau)
    copie = commande.copy()
    copie["statut"] = nouveau
    return copie


def _verifier_cles(
    donnees: dict[object, object],
    champ: str,
    obligatoires: frozenset[str],
    facultatives: frozenset[str],
) -> None:
    """Fournie. Lève ``CommandeInvalide`` si une clé obligatoire manque
    (``"articles[0].prix : champ manquant"``) ou si une clé est inconnue
    (``"articles[0] : champ inconnu 'taille'"``). ``champ`` vaut ``""`` pour
    la commande elle-même."""
    prefixe = f"{champ}." if champ else ""
    for cle in sorted(obligatoires):
        if cle not in donnees:
            raise CommandeInvalide(prefixe + cle, "champ manquant")
    inconnues = sorted(
        repr(cle) for cle in donnees if cle not in obligatoires | facultatives
    )
    if inconnues:
        raise CommandeInvalide(champ or "commande", f"champ inconnu {inconnues[0]}")


def _est_nombre(valeur: object) -> TypeGuard[int | float]:
    """Un int ou un float, mais pas un bool (True est un int en Python)."""
    return isinstance(valeur, (int, float)) and not isinstance(valeur, bool)


def _est_entier(valeur: object) -> TypeGuard[int]:
    return isinstance(valeur, int) and not isinstance(valeur, bool)


def lire_article(donnees: object, champ: str = "article") -> Article:
    """Valide un article brut et renvoie un nouvel ``Article``. ``champ``
    préfixe les messages d'erreur (``"articles[1].prix"``)."""
    if not isinstance(donnees, dict):
        raise CommandeInvalide(champ, "objet attendu")
    _verifier_cles(donnees, champ, frozenset({"nom", "prix", "quantite"}), frozenset())

    nom = donnees["nom"]
    if not isinstance(nom, str) or not nom:
        raise CommandeInvalide(f"{champ}.nom", "texte non vide attendu")
    prix = donnees["prix"]
    if not _est_nombre(prix) or not math.isfinite(prix) or prix < 0:
        raise CommandeInvalide(f"{champ}.prix", "nombre positif attendu")
    quantite = donnees["quantite"]
    if not _est_entier(quantite) or quantite < 1:
        raise CommandeInvalide(f"{champ}.quantite", "entier >= 1 attendu")
    return {"nom": nom, "prix": float(prix), "quantite": quantite}


def lire_commande(donnees: object) -> Commande:
    """Valide une commande brute (issue de ``json.loads``) et renvoie une
    nouvelle ``Commande``. Lève ``CommandeInvalide`` au premier problème."""
    if not isinstance(donnees, dict):
        raise CommandeInvalide("commande", "objet attendu")
    _verifier_cles(
        donnees,
        "",
        frozenset({"id", "client", "statut", "articles"}),
        frozenset({"remise"}),
    )

    identifiant = donnees["id"]
    if not _est_entier(identifiant):
        raise CommandeInvalide("id", "entier attendu")
    client = donnees["client"]
    if not isinstance(client, str) or not client:
        raise CommandeInvalide("client", "texte non vide attendu")
    statut = donnees["statut"]
    if not est_statut(statut):
        raise CommandeInvalide("statut", f"statut inconnu {statut!r}")
    articles_bruts = donnees["articles"]
    if not isinstance(articles_bruts, list):
        raise CommandeInvalide("articles", "liste attendue")
    articles = [
        lire_article(article, f"articles[{i}]")
        for i, article in enumerate(articles_bruts)
    ]

    commande: Commande = {
        "id": identifiant,
        "client": client,
        "statut": statut,
        "articles": articles,
    }
    if "remise" in donnees:
        remise = donnees["remise"]
        if not _est_nombre(remise) or not 0 <= remise < 1:
            raise CommandeInvalide("remise", "nombre dans [0, 1[ attendu")
        commande["remise"] = float(remise)
    return commande


def trier(
    commandes: Iterable[Commande],
    cle: Callable[[Commande], float],
    *,
    decroissant: bool = False,
) -> list[Commande]:
    """Trie les commandes selon ``cle``, une fonction qui associe un nombre à
    une commande (par exemple ``total``)."""
    return sorted(commandes, key=cle, reverse=decroissant)

"""Étape 2 : chaînage d'exceptions.

Un petit chargeur de configuration (``cle = valeur``, une par ligne) qui
traduit les erreurs techniques en erreurs métier, en gardant ou en masquant
leur cause selon qu'elle aide ou non à comprendre le problème.
"""

from collections.abc import Callable
from pathlib import Path


class ErreurConfig(Exception):
    """Base des erreurs de configuration."""


class ConfigIllisible(ErreurConfig):
    def __init__(self, chemin: str | Path) -> None:
        self.chemin = chemin
        super().__init__(f"Config illisible : {chemin}")


class LigneInvalide(ErreurConfig):
    def __init__(self, numero: int, ligne: str) -> None:
        self.numero = numero
        self.ligne = ligne
        super().__init__(f"Ligne {numero} invalide : {ligne!r}")


class CleManquante(ErreurConfig):
    def __init__(self, cle: str) -> None:
        self.cle = cle
        super().__init__(f"Clé absente : {cle}")


class ValeurInvalide(ErreurConfig):
    def __init__(self, cle: str, valeur: str) -> None:
        self.cle = cle
        self.valeur = valeur
        super().__init__(f"Valeur invalide pour {cle} : {valeur!r}")


def analyser(texte: str) -> dict[str, str]:
    """Analyse un texte de configuration : une paire ``cle = valeur`` par
    ligne, espaces retirés autour de la clé et de la valeur. Les lignes vides
    et celles qui commencent par ``#`` sont ignorées. Une ligne sans ``=``, ou
    dont la clé est vide, lève ``LigneInvalide`` (lignes numérotées à partir
    de 1), sans cause ni contexte affichés."""
    config: dict[str, str] = {}
    for numero, ligne in enumerate(texte.splitlines(), start=1):
        propre = ligne.strip()
        if not propre or propre.startswith("#"):
            continue
        cle, egal, valeur = propre.partition("=")
        cle = cle.strip()
        if not egal or not cle:
            raise LigneInvalide(numero, propre)
        config[cle] = valeur.strip()
    return config


def charger_config(chemin: str | Path) -> dict[str, str]:
    """Lit le fichier (``open(chemin, encoding="utf-8")``) et l'analyse.
    Une ``OSError`` à la lecture devient ``ConfigIllisible``, avec l'erreur
    d'origine pour cause. Une ``LigneInvalide`` se propage telle quelle."""
    try:
        with open(chemin, encoding="utf-8") as fichier:
            texte = fichier.read()
    except OSError as e:
        raise ConfigIllisible(chemin) from e
    # analyser est hors du try : ses erreurs ne sont pas des erreurs de lecture.
    return analyser(texte)


def lire_entier(config: dict[str, str], cle: str) -> int:
    """Renvoie ``int(config[cle])``. Une clé absente lève ``CleManquante``
    sans contexte affiché (le ``KeyError`` n'apprend rien de plus). Une valeur
    non entière lève ``ValeurInvalide``, causée par le ``ValueError``."""
    try:
        valeur = config[cle]
    except KeyError:
        raise CleManquante(cle) from None
    try:
        return int(valeur)
    except ValueError as e:
        raise ValeurInvalide(cle, valeur) from e


def chaine_des_causes(exc: BaseException) -> list[BaseException]:
    """Renvoie la chaîne que Python afficherait, en partant de ``exc`` :
    on suit ``__cause__`` s'il existe, sinon ``__context__``, sauf si
    ``__suppress_context__`` est vrai. On s'arrête sur une exception déjà
    vue."""
    chaine: list[BaseException] = []
    courante: BaseException | None = exc
    while courante is not None and courante not in chaine:
        chaine.append(courante)
        if courante.__cause__ is not None:
            courante = courante.__cause__
        elif not courante.__suppress_context__:
            courante = courante.__context__
        else:
            courante = None
    return chaine


def journaliser_et_relancer[T](fonction: Callable[[], T], journal: list[str]) -> T:
    """Appelle ``fonction()``. Si elle lève une ``Exception``, ajoute
    ``"<NomDuType> : <message>"`` au journal, puis relance **la même**
    exception, sans l'envelopper."""
    try:
        return fonction()
    except Exception as e:
        journal.append(f"{type(e).__name__} : {e}")
        raise

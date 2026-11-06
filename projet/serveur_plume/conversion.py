"""Convertir les objets de Plume (erreurs, tokens, arbre) en JSON pour l'IA."""

import re
from dataclasses import fields, is_dataclass

from plume.erreurs import ErreurPlume, ErreursMultiples, formater
from plume.etape1_lexer.tokens import Token

from serveur_plume.schemas import ErreurJSON, TokenJSON


def erreurs_json(erreur: ErreurPlume, source: str) -> list[ErreurJSON]:
    """Une entrée par erreur (une ErreursMultiples est aplatie)."""
    liste = erreur.erreurs if isinstance(erreur, ErreursMultiples) else [erreur]
    resultat: list[ErreurJSON] = []
    for e in liste:
        pos = e.position
        connue = pos is not None and pos.ligne > 0
        resultat.append(
            {
                "genre": e.genre,
                "message": e.message,
                "ligne": pos.ligne if pos is not None and connue else None,
                "colonne": pos.colonne if pos is not None and connue else None,
                "contexte": formater(e, source, "programme.plume"),
            }
        )
    return resultat


def token_json(jeton: Token) -> TokenJSON:
    return {
        "type": jeton.kind.name,
        "texte": jeton.lexeme,
        "ligne": jeton.position.ligne,
        "colonne": jeton.position.colonne,
    }


def noeud_json(valeur: object) -> object:
    """Convertit un nœud de l'arbre en JSON, avec son type et sa position."""
    if is_dataclass(valeur) and not isinstance(valeur, type):
        resultat: dict[str, object] = {"type": type(valeur).__name__}
        for champ in fields(valeur):
            if champ.name != "pos":
                resultat[champ.name] = noeud_json(getattr(valeur, champ.name))
        pos = getattr(valeur, "pos", None)
        if pos is not None and pos.ligne > 0:
            resultat["ligne"] = pos.ligne
            resultat["colonne"] = pos.colonne
        return resultat
    if isinstance(valeur, tuple):
        return [noeud_json(v) for v in valeur]
    if valeur is None or isinstance(valeur, bool | int | str):
        return valeur
    raise TypeError(f"valeur inattendue dans l'arbre : {valeur!r}")


def contient_un_commentaire(source: str) -> bool:
    """Vrai s'il y a un ``#`` hors d'un texte entre guillemets."""
    for trouve in re.finditer(r'"(?:\\.|[^"\\\n])*"|#', source):
        if trouve.group(0) == "#":
            return True
    return False


def erreur_depuis_stderr(stderr: str) -> ErreurJSON:
    """Reconstruit l'erreur à partir du message de la CLI :
    ``programme.plume:2:5 : erreur d'exécution : division par zéro``."""
    trouve = re.match(r"[^\n]*?:(\d+):(\d+) : ([^:\n]+) : ([^\n]*)", stderr)
    if trouve is None:
        return {
            "genre": "erreur d'exécution",
            "message": stderr.strip(),
            "ligne": None,
            "colonne": None,
            "contexte": stderr.strip(),
        }
    return {
        "genre": trouve[3],
        "message": trouve[4],
        "ligne": int(trouve[1]),
        "colonne": int(trouve[2]),
        "contexte": stderr.strip(),
    }

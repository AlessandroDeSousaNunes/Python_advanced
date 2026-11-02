"""Étape 3 : mutabilité et copies.

Aucune fonction de ce module ne modifie ses arguments (sauf ``noter``, voir sa
docstring) : elles renvoient toutes un nouvel objet.
"""

Fiche = tuple[str, str, int]


def ajouter(catalogue: list[Fiche], fiche: Fiche) -> list[Fiche]:
    """Renvoie un nouveau catalogue qui contient ``fiche`` en plus, à la fin.

    ``catalogue`` n'est pas modifié.
    """
    return catalogue + [fiche]


def retirer(catalogue: list[Fiche], titre: str) -> list[Fiche]:
    """Renvoie un nouveau catalogue sans les fiches dont le titre est ``titre``.

    ``catalogue`` n'est pas modifié.
    """
    return [fiche for fiche in catalogue if fiche[0] != titre]


def etiqueter(
    etiquettes: dict[str, list[str]], titre: str, etiquette: str
) -> dict[str, list[str]]:
    """Renvoie un nouveau dictionnaire titre -> étiquettes, où ``etiquette`` a
    été ajoutée à la fin de la liste de ``titre`` (créée si besoin).

    Ni ``etiquettes`` ni les listes qu'il contient ne sont modifiés.
    """
    copie = {cle: list(valeurs) for cle, valeurs in etiquettes.items()}
    copie.setdefault(titre, []).append(etiquette)
    return copie


def noter(
    titre: str, note: int, notes: list[tuple[str, int]] | None = None
) -> list[tuple[str, int]]:
    """Ajoute ``(titre, note)`` à ``notes`` et renvoie la liste.

    Si ``notes`` n'est pas fourni, une **nouvelle** liste est créée à chaque
    appel. Ici, contrairement aux autres fonctions, la liste fournie est
    modifiée sur place : c'est le comportement de ``list.append``.
    """
    if notes is None:
        notes = []
    notes.append((titre, note))
    return notes


def meme_catalogue(a: list[Fiche], b: list[Fiche]) -> tuple[bool, bool]:
    """Renvoie ``(memes_valeurs, meme_objet)`` : ``a`` et ``b`` ont-ils le même
    contenu, et sont-ils le même objet en mémoire ?"""
    return a == b, a is b

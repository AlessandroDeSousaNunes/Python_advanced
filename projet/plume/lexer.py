"""Le lexer : découpe le source en tokens, à la demande."""

from collections.abc import Iterator

from plume.erreurs import ErreurLexicale, Position
from plume.tokens import MOTS_CLES, SYMBOLES, Token, TokenKind

CHIFFRES = "0123456789"
BLANCS = " \t\r"
ECHAPPEMENTS = {"n": "\n", "t": "\t", '"': '"', "\\": "\\"}


def est_debut_identifiant(c: str) -> bool:
    return c.isalpha()


def est_suite_identifiant(c: str) -> bool:
    return c.isalnum() or c == "_"


def tokenize(source: str) -> Iterator[Token]:
    """Produit les tokens de ``source`` un par un, puis toujours ``FIN``.
    Lève ``ErreurLexicale`` à la position fautive."""
    i = 0
    ligne = 1
    debut_ligne = 0  # indice du premier caractère de la ligne courante

    def position(indice: int) -> Position:
        return Position(ligne, indice - debut_ligne + 1)

    while i < len(source):
        c = source[i]

        if c == "\n":
            i += 1
            ligne += 1
            debut_ligne = i
            continue
        if c in BLANCS:
            i += 1
            continue
        if c == "#":
            while i < len(source) and source[i] != "\n":
                i += 1
            continue

        debut = position(i)

        if c in CHIFFRES:
            j = i
            while j < len(source) and source[j] in CHIFFRES:
                j += 1
            if j < len(source) and est_suite_identifiant(source[j]):
                raise ErreurLexicale(
                    f"nombre mal formé : {source[i : j + 1]!r}", position(j)
                )
            yield Token(TokenKind.ENTIER, source[i:j], debut)
            i = j
            continue

        if est_debut_identifiant(c):
            j = i + 1
            while j < len(source) and est_suite_identifiant(source[j]):
                j += 1
            mot = source[i:j]
            yield Token(MOTS_CLES.get(mot, TokenKind.IDENT), mot, debut)
            i = j
            continue

        if c == "_":
            raise ErreurLexicale("un identifiant ne peut pas commencer par '_'", debut)

        if c == '"':
            j = i + 1
            morceaux: list[str] = []
            while True:
                if j >= len(source) or source[j] == "\n":
                    raise ErreurLexicale("texte non terminé : '\"' manquant", debut)
                d = source[j]
                if d == '"':
                    break
                if d == "\\":
                    suivant = source[j + 1] if j + 1 < len(source) else ""
                    if suivant not in ECHAPPEMENTS:
                        raise ErreurLexicale(
                            f"échappement invalide '\\{suivant}'", position(j)
                        )
                    morceaux.append(ECHAPPEMENTS[suivant])
                    j += 2
                    continue
                morceaux.append(d)
                j += 1
            yield Token(TokenKind.TEXTE, "".join(morceaux), debut, taille=j + 1 - i)
            i = j + 1
            continue

        for kind in SYMBOLES:
            if source.startswith(kind.value, i):
                yield Token(kind, kind.value, debut)
                i += len(kind.value)
                break
        else:
            raise ErreurLexicale(f"caractère inattendu {c!r}", debut)

    yield Token(TokenKind.FIN, "", position(i))

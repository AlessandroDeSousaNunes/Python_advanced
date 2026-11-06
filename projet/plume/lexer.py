"""Le lexer : découpe le source en tokens, à la demande.

En bref : on lit le texte caractère par caractère, avec un curseur ``i``.
À chaque tour de boucle, on regarde le caractère sous le curseur :

- une espace ou un saut de ligne : on le saute ;
- ``#`` : on saute toute la fin de la ligne (commentaire) ;
- un chiffre : on lit tous les chiffres qui suivent, c'est un nombre ;
- une lettre : on lit lettres, chiffres et ``_``, c'est un mot (mot-clé ou nom) ;
- ``"`` : on lit jusqu'au ``"`` suivant, c'est un texte ;
- sinon : on essaie les symboles (``<=``, ``+``, ``;``…), du plus long au plus court.

Chaque mot trouvé devient un ``Token`` (son type, son texte, sa position), donné
au parser avec ``yield`` : le lexer ne découpe que ce qu'on lui demande.
"""

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
    i = 0  # le curseur : l'indice du caractère qu'on est en train de lire
    ligne = 1  # le numéro de la ligne courante, pour les messages d'erreur
    debut_ligne = 0  # indice du premier caractère de la ligne courante

    def position(indice: int) -> Position:
        """Transforme un indice dans le texte en (ligne, colonne)."""
        return Position(ligne, indice - debut_ligne + 1)

    # Tant qu'il reste du texte, on lit le caractère sous le curseur.
    while i < len(source):
        c = source[i]

        # Saut de ligne : on passe à la ligne suivante, sans produire de token.
        if c == "\n":
            i += 1
            ligne += 1
            debut_ligne = i
            continue
        # Espace ou tabulation : ça ne sert qu'à séparer les mots, on la saute.
        if c in BLANCS:
            i += 1
            continue
        # Commentaire : on saute tout jusqu'à la fin de la ligne.
        if c == "#":
            while i < len(source) and source[i] != "\n":
                i += 1
            continue

        # Ici commence un vrai token : on retient sa position.
        debut = position(i)

        # Un nombre : j avance tant qu'on voit des chiffres. source[i:j] est le
        # nombre complet (par exemple "42").
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

        # Un mot : j avance tant que le caractère peut continuer un mot
        # (lettre, chiffre, _). Une espace ou un symbole l'arrête : c'est
        # comme ça que « le chat » donne deux mots, « le » et « chat ».
        if est_debut_identifiant(c):
            j = i + 1
            while j < len(source) and est_suite_identifiant(source[j]):
                j += 1
            mot = source[i:j]
            # Le mot entier d'abord, puis : est-ce un mot-clé ? Ainsi
            # « siffler » reste un nom, il n'est pas coupé en « si » + « ffler ».
            yield Token(MOTS_CLES.get(mot, TokenKind.IDENT), mot, debut)
            i = j
            continue

        if c == "_":
            raise ErreurLexicale("un identifiant ne peut pas commencer par '_'", debut)

        # Un texte : on lit jusqu'au guillemet fermant, en décodant les
        # échappements (\n devient un vrai saut de ligne). Les espaces à
        # l'intérieur font partie du texte : "le chat" est UN seul token.
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

        # Un symbole : SYMBOLES est trié du plus long au plus court, donc on
        # essaie « <= » avant « < ». Le premier qui correspond gagne.
        for kind in SYMBOLES:
            if source.startswith(kind.value, i):
                yield Token(kind, kind.value, debut)
                i += len(kind.value)
                break
        else:
            # Aucun cas n'a reconnu ce caractère (@, $, !…) : erreur.
            raise ErreurLexicale(f"caractère inattendu {c!r}", debut)

    # Toujours un token FIN à la fin : le parser sait ainsi que c'est terminé.
    yield Token(TokenKind.FIN, "", position(i))

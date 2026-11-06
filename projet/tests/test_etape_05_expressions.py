import pytest
from plume.erreurs import ErreurSyntaxe, Position
from plume.etape1_lexer.tokens import TokenKind as T
from plume.etape2_parser.noeuds import (
    Appel,
    Binaire,
    Booleen,
    Entier,
    Texte,
    Unaire,
    Variable,
)
from plume.etape2_parser.parser import INFIXES, PREFIXES, Parser, parse_expression


def b(op, gauche, droite):
    return Binaire(op, gauche, droite)


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("42", Entier(42)),
        ('"salut"', Texte("salut")),
        ("vrai", Booleen(True)),
        ("faux", Booleen(False)),
        ("x", Variable("x")),
    ],
)
def test_litteraux(source, arbre):
    assert parse_expression(source) == arbre


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("1 + 2 * 3", b("+", Entier(1), b("*", Entier(2), Entier(3)))),
        ("1 * 2 + 3", b("+", b("*", Entier(1), Entier(2)), Entier(3))),
        ("1 - 2 - 3", b("-", b("-", Entier(1), Entier(2)), Entier(3))),
        ("8 / 4 / 2", b("/", b("/", Entier(8), Entier(4)), Entier(2))),
        ("(1 + 2) * 3", b("*", b("+", Entier(1), Entier(2)), Entier(3))),
        ("1 - (2 - 3)", b("-", Entier(1), b("-", Entier(2), Entier(3)))),
        ("a < b < c", b("<", b("<", Variable("a"), Variable("b")), Variable("c"))),
        (
            "a ou b et c",
            b("ou", Variable("a"), b("et", Variable("b"), Variable("c"))),
        ),
        (
            "a + 1 == b * 2",
            b("==", b("+", Variable("a"), Entier(1)), b("*", Variable("b"), Entier(2))),
        ),
    ],
)
def test_priorites_et_associativite(source, arbre):
    assert parse_expression(source) == arbre


def test_moins_unaire_lie_fort():
    assert parse_expression("-a * b") == b(
        "*", Unaire("-", Variable("a")), Variable("b")
    )


def test_non_porte_sur_la_comparaison():
    assert parse_expression("non a == b") == Unaire(
        "non", b("==", Variable("a"), Variable("b"))
    )


def test_non_s_arrete_avant_et():
    assert parse_expression("non a et b") == b(
        "et", Unaire("non", Variable("a")), Variable("b")
    )


def test_appels():
    assert parse_expression("f()") == Appel("f", ())
    assert parse_expression("f(1, x + 2)") == Appel(
        "f", (Entier(1), b("+", Variable("x"), Entier(2)))
    )
    assert parse_expression("f(g(1)) * 2") == b(
        "*", Appel("f", (Appel("g", (Entier(1),)),)), Entier(2)
    )


def test_les_decorateurs_ont_rempli_les_tables():
    assert {T.ENTIER, T.TEXTE, T.IDENT, T.VRAI, T.FAUX, T.MOINS, T.NON} <= set(PREFIXES)
    assert INFIXES[T.PLUS][0] < INFIXES[T.FOIS][0]
    assert INFIXES[T.OU][0] < INFIXES[T.ET][0] < INFIXES[T.EGAL_EGAL][0]
    assert PREFIXES[T.ENTIER] is Parser.__dict__["_entier"]


def test_positions_sur_plusieurs_lignes():
    arbre = parse_expression("1 +\n  x")
    assert arbre.pos == Position(1, 3)
    assert arbre.gauche.pos == Position(1, 1)
    assert arbre.droite.pos == Position(2, 3)


@pytest.mark.parametrize(
    ("source", "position", "fragment"),
    [
        ("1 +", Position(1, 4), "expression attendue, trouvé la fin du fichier"),
        ("(1 + 2", Position(1, 7), "')' attendu"),
        ("* 2", Position(1, 1), "expression attendue, trouvé '*'"),
        ("1 2", Position(1, 3), "<fin> attendu après l'expression, trouvé 2"),
        ("f(1)(2)", Position(1, 5), "seule une fonction nommée"),
        ("f(1,)", Position(1, 5), "expression attendue"),
    ],
)
def test_erreurs_de_syntaxe(source, position, fragment):
    with pytest.raises(ErreurSyntaxe) as info:
        parse_expression(source)
    assert info.value.position == position
    assert fragment in info.value.message

import pytest
from plume.erreurs import ErreurLexicale, Position, formater
from plume.etape1_lexer.flux import Flux
from plume.etape1_lexer.lexer import tokenize
from plume.etape1_lexer.tokens import TokenKind as T


def types(source):
    return [jeton.kind for jeton in tokenize(source)]


def test_instruction_simple():
    assert types("soit x = 1 + 2;") == [
        T.SOIT, T.IDENT, T.EGAL, T.ENTIER, T.PLUS, T.ENTIER, T.POINT_VIRGULE, T.FIN,
    ]  # fmt: skip


def test_source_vide_donne_fin():
    assert types("") == [T.FIN]


def test_lignes_et_colonnes():
    jetons = list(tokenize("soit a = 1;\n  affiche a;"))
    assert jetons[0].position == Position(1, 1)
    assert jetons[1].position == Position(1, 6)
    affiche = jetons[5]
    assert affiche.kind is T.AFFICHE
    assert affiche.position == Position(2, 3)
    assert jetons[-1].kind is T.FIN


@pytest.mark.parametrize(
    ("source", "attendus"),
    [
        ("==", [T.EGAL_EGAL]),
        ("=", [T.EGAL]),
        ("<=", [T.INFERIEUR_EGAL]),
        ("<", [T.INFERIEUR]),
        (">=", [T.SUPERIEUR_EGAL]),
        ("!=", [T.DIFFERENT]),
        ("= =", [T.EGAL, T.EGAL]),
        ("a<=-b", [T.IDENT, T.INFERIEUR_EGAL, T.MOINS, T.IDENT]),
    ],
)
def test_symboles_composes_et_leurs_prefixes(source, attendus):
    assert types(source) == [*attendus, T.FIN]


def test_textes_decodes():
    jeton = next(tokenize(r'"a\nb\t\"c\" \\"'))
    assert jeton.kind is T.TEXTE
    assert jeton.lexeme == 'a\nb\t"c" \\'


def test_texte_vide():
    assert next(tokenize('""')).lexeme == ""


def test_commentaires_ignores():
    assert types("# rien\naffiche 1; # fin") == [
        T.AFFICHE, T.ENTIER, T.POINT_VIRGULE, T.FIN,
    ]  # fmt: skip


def test_mot_cle_pas_reconnu_dans_un_identifiant():
    assert types("sinon_si siffler sinon") == [T.IDENT, T.IDENT, T.SINON, T.FIN]


def test_identifiants_accentues():
    jeton = next(tokenize("été_2"))
    assert (jeton.kind, jeton.lexeme) == (T.IDENT, "été_2")


@pytest.mark.parametrize(
    ("source", "position", "fragment"),
    [
        ("soit x = 1 @ 2;", Position(1, 12), "caractère inattendu '@'"),
        ('affiche "abc;', Position(1, 9), "texte non terminé"),
        ('affiche "a\nb";', Position(1, 9), "texte non terminé"),
        ('"ok \\q"', Position(1, 5), "échappement invalide '\\q'"),
        ("x = 12abc;", Position(1, 7), "nombre mal formé"),
        ("soit _x = 1;", Position(1, 6), "ne peut pas commencer par '_'"),
        ("a !b", Position(1, 3), "caractère inattendu '!'"),
    ],
)
def test_erreurs_lexicales_a_la_bonne_position(source, position, fragment):
    with pytest.raises(ErreurLexicale) as info:
        list(tokenize(source))
    assert info.value.position == position
    assert fragment in info.value.message


def test_tokenize_est_paresseux():
    jetons = tokenize("1 + 2 @")
    assert [next(jetons).kind for _ in range(3)] == [T.ENTIER, T.PLUS, T.ENTIER]
    with pytest.raises(ErreurLexicale):
        next(jetons)


def source_espionne(elements, demandes):
    for element in elements:
        demandes.append(element)
        yield element


def test_flux_regarde_sans_consommer():
    flux = Flux([1, 2, 3])
    assert flux.regarde() == 1
    assert flux.regarde(2) == 3
    assert flux.regarde() == 1
    assert flux.avance() == 1
    assert flux.regarde() == 2


def test_flux_none_en_fin():
    flux = Flux([1])
    assert flux.regarde(5) is None
    assert flux.avance() == 1
    assert flux.avance() is None


def test_flux_ne_tire_que_le_necessaire():
    demandes = []
    flux = Flux(source_espionne("abcdef", demandes))
    assert demandes == []
    flux.regarde()
    assert demandes == ["a"]
    flux.regarde(2)
    assert demandes == ["a", "b", "c"]
    flux.avance()
    flux.regarde()
    assert demandes == ["a", "b", "c"]


def test_formater_place_le_chapeau_sous_la_colonne():
    source = "soit x = 1;\nsoit y = 2 @ 3;"
    with pytest.raises(ErreurLexicale) as info:
        list(tokenize(source))
    texte = formater(info.value, source, "essai.plume")
    entete, ligne, chapeau = texte.splitlines()
    assert entete == "essai.plume:2:12 : erreur lexicale : caractère inattendu '@'"
    assert ligne.strip() == "soit y = 2 @ 3;"
    assert ligne.index("@") == chapeau.index("^")

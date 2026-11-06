import dataclasses

import pytest
from plume.erreurs import Position
from plume.etape1_lexer.tokens import MOTS_CLES, SYMBOLES, Token, TokenKind


def test_position_se_lit_comme_dans_un_editeur():
    assert str(Position(3, 7)) == "ligne 3, colonne 7"


def test_token_est_immuable():
    jeton = Token(TokenKind.IDENT, "x", Position(1, 1))
    with pytest.raises(dataclasses.FrozenInstanceError):
        jeton.lexeme = "y"  # type: ignore[misc]


def test_token_est_hachable_et_comparable():
    a = Token(TokenKind.ENTIER, "42", Position(2, 5))
    b = Token(TokenKind.ENTIER, "42", Position(2, 5))
    assert a == b
    assert len({a, b}) == 1
    assert a != Token(TokenKind.ENTIER, "42", Position(2, 6))


def test_repr_sur_une_ligne_avec_type_lexeme_et_position():
    texte = repr(Token(TokenKind.TEXTE, "a\nb", Position(4, 2)))
    assert "\n" not in texte
    assert "TEXTE" in texte
    assert "'a\\nb'" in texte
    assert "4:2" in texte


def test_mots_cles_complets_et_sans_symbole():
    assert set(MOTS_CLES) == {
        "soit", "si", "sinon", "tantque", "fonction", "retourne",
        "affiche", "vrai", "faux", "et", "ou", "non",
    }  # fmt: skip
    assert all(k.est_mot_cle for k in MOTS_CLES.values())
    assert not set(MOTS_CLES.values()) & set(SYMBOLES)


def test_symboles_complets_et_sans_mot_cle():
    textes = {k.value for k in SYMBOLES}
    assert textes == {
        "+", "-", "*", "/", "%", "==", "!=", "<", "<=", ">", ">=",
        "=", "(", ")", "{", "}", ",", ";",
    }  # fmt: skip
    assert not textes & set(MOTS_CLES)


def test_un_prefixe_vient_apres_le_symbole_plus_long():
    textes = [k.value for k in SYMBOLES]
    for i, court in enumerate(textes):
        for long in textes[i + 1 :]:
            assert not (long.startswith(court) and long != court), (court, long)


@pytest.mark.parametrize(
    ("kind", "texte"),
    [
        (TokenKind.POINT_VIRGULE, "';'"),
        (TokenKind.ACC_FERMANTE, "'}'"),
        (TokenKind.SINON, "'sinon'"),
        (TokenKind.IDENT, "<identifiant>"),
        (TokenKind.ENTIER, "<entier>"),
    ],
)
def test_str_pour_les_messages_d_erreur(kind, texte):
    assert str(kind) == texte

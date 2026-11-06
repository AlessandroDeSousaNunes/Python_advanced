from functools import singledispatchmethod

import pytest
from outils import EXEMPLES, lire
from plume.erreurs import ErreurSemantique, ErreursMultiples, Position
from plume.etape2_parser.parser import parse
from plume.etape3_analyse.semantique import Analyseur, analyser
from plume.etape3_analyse.symboles import Genre, Symbole, TableSymboles


def analyse(source):
    return analyser(parse(source))


def messages(source):
    with pytest.raises(ErreursMultiples) as info:
        analyse(source)
    assert all(isinstance(e, ErreurSemantique) for e in info.value.erreurs)
    return [e.message for e in info.value.erreurs]


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
def test_les_exemples_passent(exemple):
    analyse(lire(exemple))


def test_l_analyseur_utilise_singledispatchmethod():
    assert isinstance(Analyseur.__dict__["instruction"], singledispatchmethod)
    assert isinstance(Analyseur.__dict__["expression"], singledispatchmethod)


def test_la_portee_se_referme_meme_en_cas_d_exception():
    table = TableSymboles()
    with pytest.raises(RuntimeError), table.portee():
        table.declarer(Symbole("x", Genre.VARIABLE))
        raise RuntimeError
    assert table.profondeur == 1
    assert table.chercher("x") is None


@pytest.mark.parametrize(
    ("source", "fragment"),
    [
        ("affiche x;", "variable inconnue « x »"),
        ("x = 1;", "variable inconnue « x »"),
        ("soit x = 1; soit x = 2;", "« x » est déjà déclaré (ligne 1, colonne 1)"),
        ("si vrai { soit y = 1; } affiche y;", "variable inconnue « y »"),
        ("soit x = x;", "variable inconnue « x »"),
        ("retourne 1;", "« retourne » en dehors d'une fonction"),
        ("affiche f(1);", "fonction inconnue « f »"),
        ("fonction f(a) { } f(1, 2);", "« f » attend 1 argument(s), 2 donné(s)"),
        ("affiche texte();", "« texte » attend 1 argument(s), 0 donné(s)"),
        ("soit texte = 1;", "« texte » est une fonction prédéfinie"),
        ("fonction texte() { }", "« texte » est une fonction prédéfinie"),
        ("soit x = 1; affiche x(2);", "« x » n'est pas une fonction"),
        ("fonction f() { } affiche f;", "« f » est une fonction"),
        ("fonction f() { } f = 2;", "on ne peut pas affecter à la fonction « f »"),
        ("si vrai { fonction f() { } }", "qu'au niveau principal"),
        ("fonction f() { fonction g() { } }", "qu'au niveau principal"),
        ("fonction f(a, a) { }", "« a » est déjà déclaré"),
        ("affiche g(); fonction g() { }", "fonction inconnue « g »"),
    ],
)
def test_regles(source, fragment):
    assert any(fragment in m for m in messages(source)), messages(source)


def test_toutes_les_erreurs_ensemble_avec_leur_position():
    with pytest.raises(ErreursMultiples) as info:
        analyse("affiche a;\nsoit b = 1;\n  b = c;\nretourne;")
    assert [e.position for e in info.value.erreurs] == [
        Position(1, 9),
        Position(3, 7),
        Position(4, 1),
    ]


def test_deux_blocs_freres_peuvent_reutiliser_un_nom():
    analyse("si vrai { soit x = 1; } si vrai { soit x = 2; }")


def test_une_fonction_recursive_est_acceptee():
    analyse("fonction f(n) { si n > 0 { retourne f(n - 1); } retourne 0; }")


@pytest.mark.parametrize(
    "source",
    [
        # Masquage : en Python, les deux x seraient la même variable.
        "soit x = 1; si vrai { soit x = 2; }",
        # Globale lue puis redéclarée : en Python, UnboundLocalError.
        "soit n = 1; fonction f() { affiche n; soit n = 2; }",
        # Paramètre qui porte le nom d'une globale.
        "soit n = 1; fonction f(n) { }",
    ],
)
def test_les_cas_ou_python_changerait_le_sens_sont_refuses(source):
    assert any("déjà déclaré" in m for m in messages(source))


def test_globales_modifiees_notees():
    resultat = analyse(
        """
        soit total = 0;
        soit lu = 0;
        fonction ajouter(n) {
            soit local = n;
            total = total + local;
            local = 0;
            n = 1;
            affiche lu;
        }
        fonction rien_du_tout() { }
        """
    )
    assert resultat.globales_modifiees == {
        "ajouter": frozenset({"total"}),
        "rien_du_tout": frozenset(),
    }

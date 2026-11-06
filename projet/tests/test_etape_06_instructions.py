import pytest
from plume.erreurs import ErreurLexicale, ErreursMultiples, Position
from plume.etape2_parser.noeuds import (
    Affectation,
    Affiche,
    Appel,
    Binaire,
    Declaration,
    Entier,
    ExprInstr,
    Fonction,
    Retourne,
    Si,
    TantQue,
    Texte,
    Variable,
)
from plume.etape2_parser.parser import parse


def une(source):
    """L'unique instruction du programme."""
    (instruction,) = parse(source).instructions
    return instruction


def erreurs(source):
    with pytest.raises(ErreursMultiples) as info:
        parse(source)
    return [(e.position, e.message) for e in info.value.erreurs]


@pytest.mark.parametrize(
    ("source", "arbre"),
    [
        ("soit x = 1;", Declaration("x", Entier(1))),
        ("x = x + 1;", Affectation("x", Binaire("+", Variable("x"), Entier(1)))),
        ("affiche 1;", Affiche((Entier(1),))),
        ('affiche "a", x;', Affiche((Texte("a"), Variable("x")))),
        ("saluer(1);", ExprInstr(Appel("saluer", (Entier(1),)))),
        ("tantque x { }", TantQue(Variable("x"), ())),
        ("si x { }", Si(Variable("x"), (), None)),
        ("si x { } sinon { }", Si(Variable("x"), (), ())),
        (
            "si x { } sinon si y { affiche 1; }",
            Si(Variable("x"), (), (Si(Variable("y"), (Affiche((Entier(1),)),)),)),
        ),
        ("fonction f() { }", Fonction("f", (), ())),
        (
            "fonction f(a, b) { retourne a; }",
            Fonction("f", ("a", "b"), (Retourne(Variable("a")),)),
        ),
    ],
)
def test_chaque_instruction(source, arbre):
    assert une(source) == arbre


def test_retourne_sans_valeur():
    assert une("fonction f() { retourne; }").corps == (Retourne(None),)


def test_structures_imbriquees():
    source = """
    fonction f(n) {
        si n > 0 {
            tantque n > 0 {
                n = n - 1;
            }
        }
    }
    """
    assert une(source) == Fonction(
        "f",
        ("n",),
        (
            Si(
                Binaire(">", Variable("n"), Entier(0)),
                (
                    TantQue(
                        Binaire(">", Variable("n"), Entier(0)),
                        (Affectation("n", Binaire("-", Variable("n"), Entier(1))),),
                    ),
                ),
            ),
        ),
    )


def test_les_positions_des_instructions():
    programme = parse("soit a = 1;\n  affiche a;")
    assert [i.pos for i in programme.instructions] == [Position(1, 1), Position(2, 3)]


@pytest.mark.parametrize("source", ["1 = 2;", "f(x) = 3;", "(x) + 1 = 2;"])
def test_affectation_a_une_cible_invalide(source):
    ((_, message),) = erreurs(source)
    assert "on ne peut affecter qu'à une variable" in message


def test_point_virgule_oublie_signale_en_fin_de_ligne():
    assert erreurs("soit x = 1\naffiche x;") == [
        (Position(1, 11), "';' attendu à la fin de l'instruction, trouvé 'affiche'")
    ]


def test_point_virgule_oublie_apres_un_texte():
    ((position, _),) = erreurs('affiche "été"\nsoit y = 2;')
    assert position == Position(1, 14)


def test_plusieurs_erreurs_signalees_ensemble():
    source = "soit = 1;\naffiche 2;\nsoit x = ;\naffiche (3;\n"
    assert [p for p, _ in erreurs(source)] == [
        Position(1, 6),
        Position(3, 10),
        Position(4, 11),
    ]


def test_une_erreur_dans_un_bloc_n_empeche_pas_la_suite_du_bloc():
    source = "si vrai {\n  soit = 1;\n  affiche 2 3;\n  affiche 4;\n}"
    assert [p.ligne for p, _ in erreurs(source)] == [2, 3]


def test_accolade_orpheline():
    assert erreurs("affiche 1;\n}") == [
        (Position(2, 1), "'}' en trop : aucun bloc à fermer")
    ]


def test_bloc_jamais_ferme():
    ((position, message),) = erreurs("si vrai {\n  affiche 1;\n")
    assert position == Position(3, 1)
    assert message == (
        "'}' attendu pour fermer le bloc ouvert ligne 1, trouvé la fin du fichier"
    )


def test_erreur_lexicale_dans_les_erreurs_multiples_et_chainee():
    with pytest.raises(ErreursMultiples) as info:
        parse("soit = 1;\naffiche 2 @ 3;")
    premiere, lexicale = info.value.erreurs
    assert premiere.position == Position(1, 6)
    assert isinstance(lexicale, ErreurLexicale)
    assert lexicale.position == Position(2, 11)
    assert info.value.__cause__ is premiere


def test_les_exemples_s_analysent():
    from outils import EXEMPLES, lire

    for exemple in EXEMPLES:
        assert parse(lire(exemple)).instructions

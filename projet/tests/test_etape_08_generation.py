import pytest
from outils import EXEMPLES, attendu, lire
from plume.compilateur import executer, transpiler
from plume.emetteur import Emetteur
from plume.generateur import PRELUDE


def code(source):
    """Le Python généré, sans le prélude."""
    return transpiler(source).code.removeprefix(PRELUDE)


def sortie(source, capsys):
    executer(source)
    return capsys.readouterr().out


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
def test_chaque_exemple_produit_sa_sortie_attendue(exemple, capsys):
    assert sortie(lire(exemple), capsys) == attendu(exemple)


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
def test_le_code_genere_est_du_python_valide(exemple):
    compile(transpiler(lire(exemple)).code, exemple.name, "exec")


def test_emetteur_indente_et_revient():
    e = Emetteur()
    e.ligne("if x:")
    with e.bloc():
        e.ligne("y = 1")
    e.ligne("z = 2")
    assert e.texte() == "if x:\n    y = 1\nz = 2\n"


def test_emetteur_pass_dans_un_bloc_vide():
    e = Emetteur()
    e.ligne("while x:")
    with e.bloc():
        pass
    assert e.texte() == "while x:\n    pass\n"


def test_emetteur_retrouve_son_niveau_apres_une_exception():
    e = Emetteur()
    with pytest.raises(ValueError), e.bloc():
        raise ValueError
    assert e.niveau == 0


@pytest.mark.parametrize(
    ("source", "python"),
    [
        ("soit x = 1;", "x = 1\n"),
        ("soit x = 1; x = x + 1;", "x = 1\nx = (x + 1)\n"),
        ('affiche "a", vrai;', "_affiche('a', True)\n"),
        ("tantque faux { }", "while False:\n    pass\n"),
        (
            "si vrai { affiche 1; } sinon { affiche 2; }",
            "if True:\n    _affiche(1)\nelse:\n    _affiche(2)\n",
        ),
        (
            "fonction f(a) { retourne a / 2; }",
            "def f(a):\n    return (a // 2)\n",
        ),
        ("fonction f() { retourne; } f();", "def f():\n    return\nf()\n"),
        ("affiche non -1 < 2;", "_affiche((not ((-1) < 2)))\n"),
        ("affiche texte(1);", "_affiche(_texte(1))\n"),
    ],
)
def test_traduction_des_instructions(source, python):
    assert code(source) == python


def test_les_parentheses_preservent_le_sens(capsys):
    # En Python, 3 > 2 > 1 vaut True ; en Plume, (3 > 2) > 1 vaut vrai > 1.
    assert code("affiche 3 > 2 > 1;") == "_affiche(((3 > 2) > 1))\n"
    assert sortie("affiche 3 > 2 > 1;", capsys) == "faux\n"


def test_les_noms_reserves_de_python_sont_renommes(capsys):
    source = "soit print = 1; soit class = 2; soit len = print + class; affiche len;"
    assert "_v_print = 1" in code(source)
    assert sortie(source, capsys) == "3\n"


def test_une_fonction_qui_modifie_une_globale(capsys):
    source = "soit n = 0; fonction plus() { n = n + 1; } plus(); plus(); affiche n;"
    assert "    global n\n" in code(source)
    assert sortie(source, capsys) == "2\n"


def test_l_affichage_suit_la_specification(capsys):
    source = 'fonction rien() { } affiche vrai, faux, rien(), "", 7, -3 / 2;'
    assert sortie(source, capsys) == "vrai faux rien  7 -2\n"


def test_le_code_genere_est_autonome(tmp_path):
    import subprocess
    import sys

    fichier = tmp_path / "programme.py"
    fichier.write_text(transpiler("affiche 1 + 1, vrai;").code, encoding="utf-8")
    resultat = subprocess.run(
        [sys.executable, str(fichier)], capture_output=True, text=True, check=True
    )
    assert resultat.stdout.strip() == "2 vrai"

import pytest
from outils import EXEMPLES, PROJET, lire
from plume.erreurs import ErreurBackend
from plume.etape2_parser.parser import parse
from plume.etape4_traduction.backend import Sortie
from plume.etape5_execution.cli import ERREUR_COMPILATION, OK, main
from plume.etape5_execution.compilateur import BACKENDS, executer, transpiler


def formater(source):
    return transpiler(source, "formateur").code


def test_liste_des_backends():
    assert sorted(BACKENDS) == ["formateur", "python"]
    assert BACKENDS["python"].executable
    assert not BACKENDS["formateur"].executable


def test_backend_inconnu():
    with pytest.raises(ErreurBackend, match="backend inconnu « cobol »"):
        transpiler("affiche 1;", "cobol")


class CompteurInstructions:
    """Un backend écrit dans le test : il n'a besoin que du Protocol."""

    nom = "compteur"
    extension = ".txt"
    executable = False

    def generer(self, programme, analyse):
        return Sortie(str(len(programme.instructions)))


def test_un_nouveau_backend_n_a_besoin_que_du_protocole(monkeypatch):
    monkeypatch.setitem(BACKENDS, "compteur", CompteurInstructions())
    assert transpiler("soit x = 1; affiche x; x = 2;", "compteur").code == "3"


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
def test_le_formateur_preserve_l_arbre_et_est_idempotent(exemple):
    source = lire(exemple)
    une_fois = formater(source)
    assert parse(une_fois) == parse(source)
    assert formater(une_fois) == une_fois


@pytest.mark.parametrize(
    ("source", "attendu"),
    [
        ("affiche (1 + 2) * 3;", "affiche (1 + 2) * 3;\n"),
        ("affiche 1 + (2 * 3);", "affiche 1 + 2 * 3;\n"),
        ("affiche (1 - 2) - 3;", "affiche 1 - 2 - 3;\n"),
        ("affiche 1 - (2 - 3);", "affiche 1 - (2 - 3);\n"),
        ("affiche ((vrai));", "affiche vrai;\n"),
        ("affiche non (vrai et faux);", "affiche non (vrai et faux);\n"),
        ("affiche (non vrai) == faux;", "affiche (non vrai) == faux;\n"),
        ("affiche non (1 == 2);", "affiche non 1 == 2;\n"),
        ("affiche -(1 + 2);", "affiche -(1 + 2);\n"),
        ("affiche -(-1);", "affiche - -1;\n"),
    ],
)
def test_parentheses_minimales(source, attendu):
    assert formater(source) == attendu


def test_litteraux_reecrits():
    assert formater(r'affiche "il dit \"oui\"\n\\", 007;') == (
        'affiche "il dit \\"oui\\"\\n\\\\", 7;\n'
    )


def test_presentation_canonique():
    source = "soit   x=1;si x>0{affiche x;}sinon{x=0;}fonction f(){} f();"
    assert formater(source) == (
        "soit x = 1;\n"
        "si x > 0 {\n"
        "    affiche x;\n"
        "} sinon {\n"
        "    x = 0;\n"
        "}\n"
        "fonction f() {\n"
        "}\n"
        "\n"
        "f();\n"
    )


def test_le_formateur_n_est_pas_executable(tmp_path, capsys):
    with pytest.raises(ErreurBackend, match="pas de code exécutable"):
        executer("affiche 1;", "formateur")
    fichier = tmp_path / "a.plume"
    fichier.write_text("affiche 1;", encoding="utf-8")
    assert main(["run", str(fichier), "--backend", "formateur"]) == ERREUR_COMPILATION
    assert "pas de code exécutable" in capsys.readouterr().err


def test_fmt_en_place(tmp_path):
    fichier = tmp_path / "a.plume"
    fichier.write_text("soit x=1;affiche x ;", encoding="utf-8")
    assert main(["fmt", str(fichier), "--en-place"]) == OK
    assert fichier.read_text(encoding="utf-8") == "soit x = 1;\naffiche x;\n"


def test_mypy_strict_passe():
    api = pytest.importorskip("mypy.api")
    # Le pyproject.toml du dépôt du cours active déjà --strict ; sans lui
    # (dépôt de rendu), on le demande explicitement.
    config = PROJET.parent / "pyproject.toml"
    options = ["--config-file", str(config)] if config.is_file() else ["--strict"]
    sortie, erreurs, code = api.run([*options, str(PROJET / "plume")])
    assert code == 0, sortie + erreurs

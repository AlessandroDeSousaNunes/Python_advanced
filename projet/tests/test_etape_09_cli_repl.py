import inspect
import os
import subprocess
import sys

import pytest
from outils import EXEMPLES, PROJET, attendu
from plume.erreurs import ErreurExecution, Position
from plume.etape5_execution.cli import ERREUR_COMPILATION, ERREUR_EXECUTION, OK, main
from plume.etape5_execution.compilateur import executer
from plume.etape5_execution.repl import INVITE, SUITE, Reponse, repl


@pytest.fixture
def programme(tmp_path):
    def ecrire(source, nom="essai.plume"):
        chemin = tmp_path / nom
        chemin.write_text(source, encoding="utf-8")
        return str(chemin)

    return ecrire


# --- La CLI -------------------------------------------------------------------


def test_run(programme, capsys):
    assert main(["run", programme("affiche 6 * 7;")]) == OK
    assert capsys.readouterr().out == "42\n"


def test_transpile_a_l_ecran(programme, capsys):
    assert main(["transpile", programme("soit x = 1;")]) == OK
    assert capsys.readouterr().out.endswith("x = 1\n")


def test_transpile_dans_un_fichier(programme, tmp_path, capsys):
    sortie = tmp_path / "sortie.py"
    assert main(["transpile", programme("soit x = 1;"), "-o", str(sortie)]) == OK
    assert sortie.read_text(encoding="utf-8").endswith("x = 1\n")
    assert capsys.readouterr().out == ""


def test_check(programme, capsys):
    fichier = programme("soit x = 1;")
    assert main(["check", fichier]) == OK
    assert capsys.readouterr().out == f"{fichier} : aucune erreur\n"


def test_erreur_de_compilation(programme, capsys):
    fichier = programme("soit x = 1;\naffiche y;")
    assert main(["run", fichier]) == ERREUR_COMPILATION
    erreur = capsys.readouterr().err
    assert f"{fichier}:2:9 : erreur sémantique : variable inconnue « y »" in erreur


def test_erreur_d_execution_a_la_ligne_plume_au_fond_d_un_appel(programme, capsys):
    source = (
        "fonction diviser(a, b) {\n"
        "    retourne a / b;\n"
        "}\n"
        "fonction calcul(x) {\n"
        "    retourne diviser(x, 0);\n"
        "}\n"
        "affiche calcul(5);\n"
    )
    fichier = programme(source)
    assert main(["run", fichier]) == ERREUR_EXECUTION
    erreur = capsys.readouterr().err
    assert f"{fichier}:2:5 : erreur d'exécution : division par zéro" in erreur
    assert "retourne a / b;" in erreur


def test_erreur_d_execution_chainee_a_l_exception_python():
    with pytest.raises(ErreurExecution) as info:
        executer('affiche 1 + "a";')
    assert info.value.position == Position(1, 1)
    assert isinstance(info.value.__cause__, TypeError)


def test_recursion_sans_fin():
    with pytest.raises(ErreurExecution, match="récursion"):
        executer("fonction f(n) { retourne f(n + 1); } f(0);")


def test_fichier_introuvable(tmp_path, capsys):
    assert main(["run", str(tmp_path / "absent.plume")]) == ERREUR_COMPILATION
    assert "fichier introuvable" in capsys.readouterr().err


def test_commande_inconnue(capsys):
    assert main(["danser"]) == 2
    assert "danser" in capsys.readouterr().err


@pytest.mark.parametrize("exemple", EXEMPLES[:2], ids=lambda p: p.name)
def test_python_m_plume(exemple):
    env = {**os.environ, "PYTHONPATH": str(PROJET), "PYTHONIOENCODING": "utf-8"}
    resultat = subprocess.run(
        [sys.executable, "-m", "plume", "run", str(exemple)],
        cwd=PROJET,
        env=env,
        capture_output=True,
        check=True,
    )
    texte = resultat.stdout.decode("utf-8").replace("\r\n", "\n")
    assert texte == attendu(exemple)


# --- Le REPL ------------------------------------------------------------------


def demarrer():
    session = repl()
    assert next(session) == Reponse("", INVITE)
    return session


def test_le_repl_est_un_generateur():
    assert inspect.isgeneratorfunction(repl)


def test_le_repl_garde_l_etat():
    session = demarrer()
    assert session.send("soit x = 2;") == Reponse("", INVITE)
    assert session.send("x * 21") == Reponse("42\n", INVITE)
    assert session.send("x = x + 1;") == Reponse("", INVITE)
    assert session.send("affiche x;") == Reponse("3\n", INVITE)


def test_le_repl_attend_la_fin_d_un_bloc():
    session = demarrer()
    assert session.send("fonction double(n) {") == Reponse("", SUITE)
    assert session.send("    retourne n * 2;") == Reponse("", SUITE)
    assert session.send("}") == Reponse("", INVITE)
    assert session.send("double(21)") == Reponse("42\n", INVITE)


def test_le_repl_survit_aux_erreurs():
    session = demarrer()
    session.send("soit x = 1;")
    reponse = session.send("affiche y;")
    assert "variable inconnue « y »" in reponse.sortie
    assert reponse.invite == INVITE
    reponse = session.send("affiche 1 / 0;")
    assert "division par zéro" in reponse.sortie
    assert session.send("affiche x;").sortie == "1\n"


def test_une_saisie_ratee_ne_declare_rien():
    session = demarrer()
    session.send("soit a = 1; soit b = inconnu;")
    assert "variable inconnue « a »" in session.send("affiche a;").sortie
    assert session.send("soit a = 5; affiche a;").sortie == "5\n"

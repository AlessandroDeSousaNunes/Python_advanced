"""Extension 13 : les source maps."""

import json

import pytest
from outils import EXEMPLES, lire
from plume.erreurs import ErreurExecution, Position
from plume.etape4_traduction.generateur import PRELUDE
from plume.etape4_traduction.sourcemap import SourceMap
from plume.etape5_execution.cli import main
from plume.etape5_execution.compilateur import executer, transpiler

NB_LIGNES_PRELUDE = len(PRELUDE.splitlines())


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
def test_chaque_ligne_du_programme_a_une_ligne_source(exemple):
    source = lire(exemple)
    sortie = transpiler(source)
    carte = sortie.sourcemap
    assert carte is not None
    lignes_python = sortie.code.splitlines()
    nb_lignes_plume = len(source.splitlines())
    for numero, texte in enumerate(lignes_python, start=1):
        if numero <= NB_LIGNES_PRELUDE or not texte.strip():
            continue
        ligne = carte.ligne_source(numero)
        assert ligne is not None, f"ligne Python {numero} sans source : {texte!r}"
        assert 1 <= ligne <= nb_lignes_plume


def test_les_lignes_du_prelude_n_ont_pas_de_ligne_source():
    carte = transpiler("affiche 1;").sourcemap
    assert carte is not None
    for numero in range(1, NB_LIGNES_PRELUDE + 1):
        assert carte.ligne_source(numero) is None
    assert carte.ligne_source(NB_LIGNES_PRELUDE + 1) == 1


def test_l_erreur_pointe_la_ligne_la_plus_profonde():
    source = """\
fonction diviser(a, b) {
    retourne a / b;
}
fonction moitie_de_rien(x) {
    retourne diviser(x, 0);
}
affiche moitie_de_rien(4);
"""
    with pytest.raises(ErreurExecution) as erreur:
        executer(source)
    assert erreur.value.position is not None
    assert erreur.value.position.ligne == 2  # dans diviser, pas ligne 5 ni 7


def test_aller_retour_json():
    carte = SourceMap("essai.plume", {10: Position(1, 1), 11: Position(3, 5)})
    texte = json.dumps(carte.vers_json())
    assert SourceMap.depuis_json(json.loads(texte)) == carte
    assert json.loads(texte)["lignes"] == {"10": [1, 1], "11": [3, 5]}


def test_une_version_inconnue_est_refusee():
    donnees = SourceMap().vers_json()
    donnees["version"] = 2  # type: ignore[typeddict-item]
    with pytest.raises(ValueError, match="version"):
        SourceMap.depuis_json(donnees)


def test_decaler_ne_touche_que_les_lignes_python():
    carte = SourceMap("a.plume", {1: Position(1, 1), 4: Position(2, 3)})
    decalee = carte.decaler(10)
    assert decalee.lignes == {11: Position(1, 1), 14: Position(2, 3)}
    assert decalee.source == "a.plume"
    assert carte.lignes == {1: Position(1, 1), 4: Position(2, 3)}  # intacte


def test_le_formateur_n_a_pas_de_source_map():
    assert transpiler("affiche 1;", "formateur").sourcemap is None


def test_transpile_sourcemap_ecrit_le_json_a_cote(tmp_path):
    programme = tmp_path / "carres.plume"
    programme.write_text(lire(EXEMPLES[0]), encoding="utf-8")
    sortie = tmp_path / "carres.py"
    code = main(["transpile", str(programme), "-o", str(sortie), "--sourcemap"])
    assert code == 0
    fichier_map = tmp_path / "carres.py.map.json"
    donnees = json.loads(fichier_map.read_text(encoding="utf-8"))
    assert donnees["version"] == 1
    assert donnees["source"] == "carres.plume"
    carte = SourceMap.depuis_json(donnees)
    assert carte.lignes == transpiler(lire(EXEMPLES[0])).sourcemap.lignes


def test_sourcemap_sans_fichier_de_sortie_est_refuse(tmp_path, capsys):
    programme = tmp_path / "a.plume"
    programme.write_text("affiche 1;", encoding="utf-8")
    assert main(["transpile", str(programme), "--sourcemap"]) == 1
    assert "--sourcemap" in capsys.readouterr().err

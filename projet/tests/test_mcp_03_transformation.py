"""Étape 3 du MCP : transpile et format."""

import pytest
from outils import EXEMPLES, attendu, lire
from plume.etape5_execution.compilateur import BACKENDS, analyser_syntaxe
from serveur_plume.serveur import mcp

from mcp import Client

pytestmark = pytest.mark.anyio


async def appeler(outil, **arguments):
    async with Client(mcp) as client:
        return await client.call_tool(outil, arguments)


async def test_transpile_donne_du_python_executable(capsys):
    exemple = EXEMPLES[0]
    r = (await appeler("transpile", source=lire(exemple))).structured_content
    assert r["ok"] and r["correspondances"]
    exec(compile(r["code"], "<test>", "exec"), {})
    assert capsys.readouterr().out == attendu(exemple)


async def test_pas_de_correspondances_pour_un_backend_non_python():
    r = await appeler("transpile", source="affiche 1;", backend="formateur")
    assert r.structured_content["correspondances"] is None


@pytest.mark.parametrize("backend", sorted(BACKENDS))
async def test_chaque_backend_est_accessible(backend):
    r = await appeler("transpile", source="affiche 1;", backend=backend)
    assert not r.is_error and r.structured_content["ok"]


async def test_transpile_programme_faux():
    r = (await appeler("transpile", source="affiche y;")).structured_content
    assert not r["ok"] and r["erreurs"]


async def test_backend_inconnu_est_un_echec_de_l_outil():
    r = await appeler("transpile", source="affiche 1;", backend="cobol")
    assert r.is_error
    assert "formateur, python" in r.content[0].text


async def test_format_met_en_forme_et_est_idempotent():
    r = (await appeler("format", source="soit x=1;affiche x;")).structured_content
    assert r["ok"] and r["modifie"]
    assert r["code"] == "soit x = 1;\naffiche x;\n"
    r2 = (await appeler("format", source=r["code"])).structured_content
    assert not r2["modifie"]


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
async def test_format_preserve_l_arbre(exemple):
    source = lire(exemple)
    r = (await appeler("format", source=source)).structured_content
    assert analyser_syntaxe(r["code"]) == analyser_syntaxe(source)


async def test_format_previent_de_la_perte_des_commentaires():
    r = (await appeler("format", source="# salut\nsoit x=1;")).structured_content
    assert "commentaires" in r["avertissement"]
    r2 = (await appeler("format", source='affiche "#1";\n')).structured_content
    assert r2["avertissement"] is None


async def test_format_programme_faux():
    r = (await appeler("format", source="soit = ;")).structured_content
    assert not r["ok"] and r["erreurs"]

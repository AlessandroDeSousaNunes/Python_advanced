"""Les tests du serveur MCP : on s'y connecte comme une IA, avec ``mcp.Client``."""

import json
import sys

import pytest
from outils import EXEMPLES, PROJET, attendu, lire
from plume.etape2_parser.noeuds import Entier, Texte, Variable
from serveur_plume import bac_a_sable
from serveur_plume.serveur import mcp, noeud_json

from mcp import Client, StdioServerParameters

pytestmark = pytest.mark.anyio


async def appeler(outil, **arguments):
    async with Client(mcp) as client:
        return await client.call_tool(outil, arguments)


# --- Les outils annoncés ------------------------------------------------------


async def test_les_outils_annonces():
    async with Client(mcp) as client:
        outils = {o.name: o for o in (await client.list_tools()).tools}
        assert client.instructions is not None
        assert "plume://specification" in client.instructions
    assert set(outils) == {"tokenize", "parse", "check", "transpile", "format", "run"}
    for nom in ("tokenize", "parse", "check", "transpile", "format"):
        assert outils[nom].annotations.read_only_hint
    assert outils["run"].annotations.destructive_hint is False
    assert set(outils["check"].output_schema["properties"]) == {"ok", "erreurs"}


# --- tokenize, parse, check ---------------------------------------------------


async def test_tokenize_avec_les_positions():
    r = await appeler("tokenize", source="soit x = 2;")
    tokens = r.structured_content["tokens"]
    assert [t["type"] for t in tokens][:3] == ["SOIT", "IDENT", "EGAL"]
    assert tokens[1] == {"type": "IDENT", "texte": "x", "ligne": 1, "colonne": 6}


async def test_tokenize_garde_les_tokens_avant_l_erreur():
    r = (await appeler("tokenize", source="soit x = @;")).structured_content
    assert not r["ok"]
    assert [t["texte"] for t in r["tokens"]] == ["soit", "x", "="]
    assert r["erreurs"][0]["colonne"] == 10


def test_noeud_json():
    assert noeud_json(Variable("x")) == {"type": "Variable", "nom": "x"}
    assert noeud_json(Texte("x")) != noeud_json(Variable("x"))
    json.dumps(noeud_json(Entier(1)))
    with pytest.raises(TypeError):
        noeud_json(object())


async def test_parse_ne_fait_pas_l_analyse_mais_check_si():
    source = "affiche inconnue;"
    parse = (await appeler("parse", source=source)).structured_content
    check = (await appeler("check", source=source)).structured_content
    assert parse["ok"] and parse["arbre"]["type"] == "Programme"
    assert not check["ok"]
    assert check["erreurs"][0]["message"] == "variable inconnue « inconnue »"


async def test_check_toutes_les_erreurs_sans_echec_de_l_outil():
    r = await appeler("check", source="soit = 1;\naffiche 2 3;")
    assert not r.is_error
    erreurs = r.structured_content["erreurs"]
    assert [(e["ligne"], e["colonne"]) for e in erreurs] == [(1, 6), (2, 10)]


async def test_check_ok():
    r = await appeler("check", source="soit x = 1; affiche x;")
    assert r.structured_content == {"ok": True, "erreurs": []}


# --- transpile, format --------------------------------------------------------


async def test_transpile_donne_du_python_executable(capsys):
    exemple = EXEMPLES[0]
    r = (await appeler("transpile", source=lire(exemple))).structured_content
    assert r["ok"] and r["correspondances"]
    exec(compile(r["code"], "<test>", "exec"), {})
    assert capsys.readouterr().out == attendu(exemple)


async def test_transpile_backend_inconnu_est_un_echec():
    r = await appeler("transpile", source="affiche 1;", backend="cobol")
    assert r.is_error
    assert "formateur, python" in r.content[0].text


async def test_transpile_formateur_sans_correspondances():
    r = await appeler("transpile", source="affiche 1;", backend="formateur")
    assert r.structured_content["correspondances"] is None


async def test_format_idempotent_et_avertit_des_commentaires():
    r = (await appeler("format", source="# salut\nsoit x=1;")).structured_content
    assert r["code"] == "soit x = 1;\n" and r["modifie"]
    assert "commentaires" in r["avertissement"]
    r2 = (await appeler("format", source=r["code"])).structured_content
    assert not r2["modifie"] and r2["avertissement"] is None
    r3 = (await appeler("format", source='affiche "#1";\n')).structured_content
    assert r3["avertissement"] is None


# --- run ----------------------------------------------------------------------


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
async def test_run_chaque_exemple(exemple):
    r = (await appeler("run", source=lire(exemple))).structured_content
    assert r["statut"] == "ok"
    assert r["sortie"] == attendu(exemple)


async def test_run_erreur_de_compilation_sans_processus():
    r = (await appeler("run", source="affiche y;")).structured_content
    assert r["statut"] == "erreur_compilation" and r["duree"] == 0.0


async def test_run_erreur_d_execution_avec_sa_ligne():
    r = (await appeler("run", source="soit a = 1;\naffiche a / 0;")).structured_content
    assert r["statut"] == "erreur_execution"
    assert r["erreurs"][0]["ligne"] == 2
    assert r["erreurs"][0]["message"] == "division par zéro"


async def test_run_boucle_infinie_interrompue():
    r = await appeler("run", source="tantque vrai { }", delai=1.0)
    assert r.structured_content["statut"] == "delai_depasse"
    assert r.structured_content["duree"] < 5


async def test_run_sortie_infinie_tronquee():
    r = (
        await appeler("run", source='tantque vrai { affiche "bla"; }')
    ).structured_content
    assert r["statut"] == "sortie_tronquee"
    assert len(r["sortie"].encode()) <= bac_a_sable.LIMITE


async def test_run_delai_hors_bornes_refuse():
    assert (await appeler("run", source="affiche 1;", delai=60)).is_error


def test_le_fils_ne_voit_pas_les_secrets_du_serveur(monkeypatch, tmp_path):
    monkeypatch.setenv("SECRET_DU_SERVEUR", "motdepasse")
    commande = [
        sys.executable,
        "-c",
        "import os; print(os.environ.get('SECRET_DU_SERVEUR'))",
    ]
    with bac_a_sable.processus(commande, tmp_path) as fils:
        sortie, _ = fils.communicate(timeout=10)
    assert sortie.decode().strip() == "None"


def test_le_processus_est_tue_meme_en_cas_d_exception(tmp_path):
    commande = [sys.executable, "-c", "import time; time.sleep(30)"]
    with pytest.raises(RuntimeError), bac_a_sable.processus(commande, tmp_path) as fils:
        raise RuntimeError
    assert fils.poll() is not None


# --- Ressources et prompts ----------------------------------------------------


async def test_ressources():
    async with Client(mcp) as client:
        uris = {str(r.uri) for r in (await client.list_resources()).resources}
        modeles = {
            m.uri_template
            for m in (await client.list_resource_templates()).resource_templates
        }
        spec = (await client.read_resource("plume://specification")).contents[0]
        index = (await client.read_resource("plume://exemples")).contents[0]
        ex = (await client.read_resource("plume://exemples/01_bonjour")).contents[0]
        att = (
            await client.read_resource("plume://exemples/01_bonjour/attendu")
        ).contents[0]
    assert {"plume://specification", "plume://exemples"} <= uris
    assert "plume://exemples/{nom}" in modeles
    assert spec.text == lire(PROJET / "specification.md")
    for exemple in EXEMPLES:
        assert f"plume://exemples/{exemple.stem}" in index.text
    assert ex.text == lire(EXEMPLES[0])
    assert att.text == attendu(EXEMPLES[0])


@pytest.mark.parametrize("nom", ["inconnu", "../specification", "..%2F..%2Fpyproject"])
async def test_traversee_de_chemin_refusee(nom):
    async with Client(mcp) as client:
        with pytest.raises(Exception):  # noqa: B017
            await client.read_resource(f"plume://exemples/{nom}")


async def test_prompts():
    async with Client(mcp) as client:
        noms = {p.name for p in (await client.list_prompts()).prompts}
        ecrire = await client.get_prompt(
            "ecrire_programme", {"tache": "compter jusqu'à 3"}
        )
        corriger = await client.get_prompt(
            "corriger_programme",
            {"source": "affiche y;", "erreurs": "variable inconnue"},
        )
    assert noms == {"ecrire_programme", "corriger_programme"}
    texte = ecrire.messages[0].content.text
    assert "compter jusqu'à 3" in texte and "plume://specification" in texte
    texte = corriger.messages[0].content.text
    assert "affiche y;" in texte and "variable inconnue" in texte


# --- Le vrai serveur, en stdio --------------------------------------------------


async def test_le_serveur_demarre_en_stdio():
    parametres = StdioServerParameters(
        command=sys.executable, args=["-m", "serveur_plume"], cwd=str(PROJET)
    )
    async with Client(parametres, read_timeout_seconds=30) as client:
        assert client.server_info.name == "plume"
        r = await client.call_tool("check", {"source": "affiche 1;"})
    assert r.structured_content["ok"]


def test_l_exemple_de_configuration():
    config = json.loads(lire(PROJET / "mcp.exemple.json"))
    assert config["mcpServers"]["plume"]["args"] == ["-m", "serveur_plume"]

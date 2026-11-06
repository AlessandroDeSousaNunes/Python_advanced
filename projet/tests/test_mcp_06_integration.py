"""Étape 6 du MCP : le vrai serveur en stdio, et le scénario de l'exercice final."""

import json
import sys

import pytest
from outils import PROJET, lire
from serveur_plume.serveur import mcp

from mcp import Client, StdioServerParameters

pytestmark = pytest.mark.anyio


async def test_le_vrai_serveur_demarre_en_stdio():
    parametres = StdioServerParameters(
        command=sys.executable, args=["-m", "serveur_plume"], cwd=str(PROJET)
    )
    async with Client(parametres, read_timeout_seconds=30) as client:
        assert client.server_info is not None
        assert client.server_info.name == "plume"
        outils = {o.name for o in (await client.list_tools()).tools}
        r = await client.call_tool("check", {"source": "affiche 1;"})
    assert "run" in outils
    assert r.structured_content["ok"]


def test_l_exemple_de_configuration_est_valide():
    config = json.loads(lire(PROJET / "mcp.exemple.json"))
    serveur = config["mcpServers"]["plume"]
    assert serveur["args"] == ["-m", "serveur_plume"]
    assert serveur["command"].endswith(("python", "python.exe"))
    assert "projet" in serveur["env"]["PYTHONPATH"]


# --- Le scénario : une « IA » scriptée qui ne connaît Plume que par le serveur ---

# Premier jet : un « ; » oublié ligne 5, et une faute de frappe ligne 7 (nb au
# lieu de i). Deux fautes typiques d'un débutant en Plume.
PREMIER_JET = """\
# Les carrés de 1 à 5
fonction carre(n) {
    retourne n * n;
}
soit i = 1
tantque i <= 5 {
    affiche i, carre(nb);
    i = i + 1;
}
"""
DEUXIEME_JET = PREMIER_JET.replace("soit i = 1\n", "soit i = 1;\n")
VERSION_FINALE = DEUXIEME_JET.replace("carre(nb)", "carre(i)")
SORTIE = "1 1\n2 4\n3 9\n4 16\n5 25\n"


async def test_scenario_de_l_exercice_final():
    async with Client(mcp) as ia:
        # 1. Découvrir le langage : instructions, spécification, un exemple.
        assert ia.instructions is not None
        assert "plume://specification" in ia.instructions
        spec = (await ia.read_resource("plume://specification")).contents[0]
        assert "tantque" in spec.text
        index = (await ia.read_resource("plume://exemples")).contents[0]
        assert "plume://exemples/03_boucles" in index.text
        exemple = (await ia.read_resource("plume://exemples/03_boucles")).contents[0]
        assert "tantque" in exemple.text

        # 2. Premier jet : le « ; » oublié est signalé, ligne 5.
        r = (await ia.call_tool("check", {"source": PREMIER_JET})).structured_content
        assert not r["ok"]
        assert r["erreurs"][0]["genre"] == "erreur de syntaxe"
        assert r["erreurs"][0]["ligne"] == 5
        assert "';' attendu" in r["erreurs"][0]["message"]

        # 3. Corrigé : check trouve maintenant la faute de frappe, ligne 7.
        r = (await ia.call_tool("check", {"source": DEUXIEME_JET})).structured_content
        assert not r["ok"]
        assert r["erreurs"][0]["ligne"] == 7
        assert "nb" in r["erreurs"][0]["message"]

        # 4. Corrigé : check dit ok, et run donne la bonne sortie.
        r = (await ia.call_tool("check", {"source": VERSION_FINALE})).structured_content
        assert r["ok"]
        r = (await ia.call_tool("run", {"source": VERSION_FINALE})).structured_content
        assert r["statut"] == "ok" and r["sortie"] == SORTIE

        # 5. format, et la version formatée donne la même sortie.
        forme = await ia.call_tool("format", {"source": VERSION_FINALE})
        assert forme.structured_content["ok"]
        code = forme.structured_content["code"]
        r = (await ia.call_tool("run", {"source": code})).structured_content
        assert r["sortie"] == SORTIE

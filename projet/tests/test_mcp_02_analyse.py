"""Étape 2 du MCP : tokenize, parse, check."""

import json

import pytest
from plume.etape2_parser.noeuds import Entier, Texte, Variable
from plume.etape5_execution.compilateur import analyser_syntaxe
from serveur_plume.conversion import noeud_json
from serveur_plume.serveur import mcp

from mcp import Client

pytestmark = pytest.mark.anyio


async def appeler(outil, **arguments):
    async with Client(mcp) as client:
        return await client.call_tool(outil, arguments)


def test_noeud_json_garde_le_type_et_distingue_deux_noeuds():
    assert noeud_json(Variable("x")) == {"type": "Variable", "nom": "x"}
    assert noeud_json(Texte("x")) != noeud_json(Variable("x"))


def test_noeud_json_ajoute_la_position_et_reste_serialisable():
    arbre = noeud_json(analyser_syntaxe("soit x = 1 + y;"))
    assert isinstance(arbre, dict)
    declaration = arbre["instructions"][0]
    assert declaration["type"] == "Declaration"
    assert (declaration["ligne"], declaration["colonne"]) == (1, 1)
    json.dumps(arbre)
    json.dumps(noeud_json(Entier(1)))


def test_noeud_json_refuse_une_valeur_inattendue():
    with pytest.raises(TypeError):
        noeud_json(object())


async def test_les_outils_d_analyse_sont_en_lecture_seule():
    async with Client(mcp) as client:
        assert client.instructions is not None
        assert "plume://specification" in client.instructions
        outils = {o.name: o for o in (await client.list_tools()).tools}
    for nom in ("tokenize", "parse", "check"):
        assert outils[nom].annotations.read_only_hint


async def test_le_schema_de_sortie_de_check_vient_du_typeddict():
    async with Client(mcp) as client:
        outils = {o.name: o for o in (await client.list_tools()).tools}
    assert set(outils["check"].output_schema["properties"]) == {"ok", "erreurs"}


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


async def test_parse_renvoie_l_arbre():
    r = (await appeler("parse", source="affiche 1;")).structured_content
    assert r["ok"] and r["arbre"]["type"] == "Programme"
    assert r["arbre"]["instructions"][0]["type"] == "Affiche"


async def test_parse_renvoie_toutes_les_erreurs_de_syntaxe():
    r = (await appeler("parse", source="soit = 1;\naffiche 2 3;")).structured_content
    assert not r["ok"] and r["arbre"] is None
    assert [e["ligne"] for e in r["erreurs"]] == [1, 2]


async def test_parse_ne_fait_pas_l_analyse_mais_check_si():
    source = "affiche inconnue;"
    resultat_parse = (await appeler("parse", source=source)).structured_content
    check = (await appeler("check", source=source)).structured_content
    assert resultat_parse["ok"]
    assert not check["ok"]
    assert check["erreurs"][0]["message"] == "variable inconnue « inconnue »"


async def test_check_toutes_les_erreurs_sans_echec_de_l_outil():
    r = await appeler("check", source="soit = 1;\naffiche 2 3;")
    assert not r.is_error
    erreurs = r.structured_content["erreurs"]
    assert [(e["ligne"], e["colonne"]) for e in erreurs] == [(1, 6), (2, 10)]
    assert all(e["genre"] == "erreur de syntaxe" for e in erreurs)
    assert "^" in erreurs[0]["contexte"]


async def test_check_ok():
    r = await appeler("check", source="soit x = 1; affiche x;")
    assert r.structured_content == {"ok": True, "erreurs": []}

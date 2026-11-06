"""Étape 1 du MCP : le serveur « bonjour »."""

import pytest
from serveur_plume.bonjour import mcp, saluer

from mcp import Client

pytestmark = pytest.mark.anyio


def test_le_decorateur_rend_la_fonction_intacte():
    assert saluer("Ada") == "Bonjour, Ada !"


async def test_les_outils_et_leur_description():
    async with Client(mcp) as client:
        outils = {o.name: o for o in (await client.list_tools()).tools}
    assert set(outils) == {"saluer", "additionner", "repeter"}
    assert outils["saluer"].description == "Salue une personne par son prénom."
    assert outils["additionner"].description == "Additionne deux entiers."


async def test_le_schema_reflete_les_annotations():
    async with Client(mcp) as client:
        outils = {o.name: o for o in (await client.list_tools()).tools}
    saluer_schema = outils["saluer"].input_schema
    assert saluer_schema["required"] == ["nom"]
    assert saluer_schema["properties"]["nom"]["type"] == "string"
    assert saluer_schema["properties"]["nom"]["description"] == "Prénom de la personne"
    additionner_schema = outils["additionner"].input_schema
    assert additionner_schema["properties"]["a"]["type"] == "integer"
    repeter_schema = outils["repeter"].input_schema
    assert repeter_schema["required"] == ["mot"]  # « fois » est facultatif
    assert repeter_schema["properties"]["fois"]["default"] == 2


async def test_un_appel_renvoie_texte_et_contenu_structure():
    async with Client(mcp) as client:
        somme = await client.call_tool("additionner", {"a": 40, "b": 2})
        bonjour = await client.call_tool("saluer", {"nom": "Ada"})
    assert not somme.is_error
    assert somme.structured_content == {"result": 42}
    assert somme.content[0].text == "42"
    assert bonjour.structured_content == {"result": "Bonjour, Ada !"}


@pytest.mark.parametrize(
    "arguments", [{"a": "quarante", "b": 2}, {"a": 1}], ids=["mauvais_type", "manquant"]
)
async def test_des_arguments_invalides_sont_un_echec_de_l_outil(arguments):
    async with Client(mcp) as client:
        resultat = await client.call_tool("additionner", arguments)
    assert resultat.is_error


async def test_les_instructions_sont_transmises():
    async with Client(mcp) as client:
        assert client.instructions is not None
        assert "additionner" in client.instructions

"""Étape 5 du MCP : resources et prompts."""

import pytest
from outils import EXEMPLES, PROJET, attendu, lire
from serveur_plume.serveur import mcp

from mcp import Client

pytestmark = pytest.mark.anyio


async def test_resources_et_modeles_listes_avec_leur_type_mime():
    async with Client(mcp) as client:
        ressources = {str(r.uri): r for r in (await client.list_resources()).resources}
        modeles = {
            m.uri_template: m
            for m in (await client.list_resource_templates()).resource_templates
        }
    assert ressources["plume://specification"].mime_type == "text/markdown"
    assert ressources["plume://exemples"].mime_type == "text/markdown"
    assert modeles["plume://exemples/{nom}"].mime_type == "text/plain"
    assert modeles["plume://exemples/{nom}/attendu"].mime_type == "text/plain"


async def test_la_specification_est_identique_au_fichier():
    async with Client(mcp) as client:
        spec = (await client.read_resource("plume://specification")).contents[0]
    assert spec.text == lire(PROJET / "specification.md")


async def test_l_index_liste_tous_les_exemples():
    async with Client(mcp) as client:
        index = (await client.read_resource("plume://exemples")).contents[0]
    for exemple in EXEMPLES:
        assert f"plume://exemples/{exemple.stem}" in index.text


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
async def test_chaque_exemple_et_sa_sortie_sont_lisibles(exemple):
    async with Client(mcp) as client:
        uri = f"plume://exemples/{exemple.stem}"
        source = (await client.read_resource(uri)).contents[0]
        sortie = (await client.read_resource(f"{uri}/attendu")).contents[0]
    assert source.text == lire(exemple)
    assert sortie.text == attendu(exemple)


@pytest.mark.parametrize("nom", ["inconnu", "../specification", "..%2F..%2Fpyproject"])
async def test_nom_inconnu_et_traversee_de_chemin_refuses(nom):
    async with Client(mcp) as client:
        with pytest.raises(Exception):  # noqa: B017
            await client.read_resource(f"plume://exemples/{nom}")


async def test_les_prompts_et_leurs_parametres():
    async with Client(mcp) as client:
        prompts = {p.name: p for p in (await client.list_prompts()).prompts}
    assert set(prompts) == {"ecrire_programme", "corriger_programme"}
    assert [a.name for a in prompts["ecrire_programme"].arguments] == ["tache"]
    assert [a.name for a in prompts["corriger_programme"].arguments] == [
        "source",
        "erreurs",
    ]


async def test_ecrire_programme_contient_la_tache_et_la_methode():
    async with Client(mcp) as client:
        r = await client.get_prompt("ecrire_programme", {"tache": "compter jusqu'à 3"})
    texte = r.messages[0].content.text
    assert "compter jusqu'à 3" in texte
    assert "plume://specification" in texte
    assert "check" in texte and "run" in texte


async def test_corriger_programme_contient_le_source_et_les_erreurs():
    async with Client(mcp) as client:
        r = await client.get_prompt(
            "corriger_programme",
            {"source": "affiche y;", "erreurs": "variable inconnue"},
        )
    texte = r.messages[0].content.text
    assert "affiche y;" in texte and "variable inconnue" in texte

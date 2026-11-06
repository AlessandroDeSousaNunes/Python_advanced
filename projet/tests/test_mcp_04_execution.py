"""Étape 4 du MCP : l'outil run, exécuté dans un sous-processus borné."""

import sys
from pathlib import Path

import pytest
from outils import EXEMPLES, attendu, lire
from serveur_plume import bac_a_sable
from serveur_plume.serveur import mcp

from mcp import Client

pytestmark = pytest.mark.anyio


async def appeler(outil, **arguments):
    async with Client(mcp) as client:
        return await client.call_tool(outil, arguments)


@pytest.mark.parametrize("exemple", EXEMPLES, ids=lambda p: p.name)
async def test_chaque_exemple(exemple):
    r = (await appeler("run", source=lire(exemple))).structured_content
    assert r["statut"] == "ok"
    assert r["sortie"] == attendu(exemple)


async def test_erreur_de_compilation_sans_processus():
    r = (await appeler("run", source="affiche y;")).structured_content
    assert r["statut"] == "erreur_compilation" and r["duree"] == 0.0


async def test_erreur_d_execution_avec_sa_ligne():
    r = (await appeler("run", source="soit a = 1;\naffiche a / 0;")).structured_content
    assert r["statut"] == "erreur_execution"
    assert r["erreurs"][0]["ligne"] == 2
    assert r["erreurs"][0]["message"] == "division par zéro"


async def test_boucle_infinie_interrompue():
    r = await appeler("run", source="tantque vrai { }", delai=1.0)
    assert r.structured_content["statut"] == "delai_depasse"
    assert r.structured_content["duree"] < 5


async def test_sortie_infinie_tronquee():
    r = (
        await appeler("run", source='tantque vrai { affiche "bla"; }')
    ).structured_content
    assert r["statut"] == "sortie_tronquee"
    assert len(r["sortie"].encode()) <= bac_a_sable.LIMITE


@pytest.mark.skipif(sys.platform == "win32", reason="RLIMIT_AS : POSIX seulement")
async def test_memoire_excessive_arretee():
    source = "soit x = 2; tantque vrai { x = x * x; }"
    r = (await appeler("run", source=source, delai=10.0)).structured_content
    assert r["statut"] == "memoire_depassee"


@pytest.mark.parametrize("delai", [0.0, 60])
async def test_delai_hors_bornes_refuse(delai):
    assert (await appeler("run", source="affiche 1;", delai=delai)).is_error


async def test_run_sans_effet_de_bord():
    async with Client(mcp) as client:
        outils = {o.name: o for o in (await client.list_tools()).tools}
    assert outils["run"].annotations.destructive_hint is False
    assert outils["run"].annotations.open_world_hint is False


def test_le_dossier_temporaire_est_supprime(monkeypatch):
    dossiers: list[Path] = []
    vrai = bac_a_sable.tempfile.TemporaryDirectory

    def espion(*args, **kwargs):
        dossier = vrai(*args, **kwargs)
        dossiers.append(Path(dossier.name))
        return dossier

    monkeypatch.setattr(bac_a_sable.tempfile, "TemporaryDirectory", espion)
    assert bac_a_sable.executer("affiche 1;").stdout == "1\n"
    assert dossiers and not dossiers[0].exists()


def test_le_processus_est_tue_meme_en_cas_d_exception(tmp_path):
    commande = [sys.executable, "-c", "import time; time.sleep(30)"]
    with pytest.raises(RuntimeError), bac_a_sable.processus(commande, tmp_path) as fils:
        raise RuntimeError
    assert fils.poll() is not None
    assert fils.stdout is not None and fils.stdout.closed


def test_le_fils_ne_lit_pas_l_entree_du_serveur(tmp_path):
    commande = [sys.executable, "-c", "import sys; print(repr(sys.stdin.read()))"]
    with bac_a_sable.processus(commande, tmp_path) as fils:
        sortie, _ = fils.communicate(timeout=10)
    assert sortie.decode().strip() == "''"


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

"""Démo du serveur MCP, sans IA : ce script joue le rôle de l'IA.

Il se branche sur le vrai serveur (comme le ferait Claude), puis appuie sur les
boutons un par un, en affichant chaque question et chaque réponse.

Lancement, depuis le dossier ``projet`` :

    python demo_mcp.py

Appuie sur Entrée pour passer à l'étape suivante.
"""

import json
import sys

import anyio

from mcp import Client, StdioServerParameters

PROGRAMME_FAUX = """soit i = 1;
tantque i <= 3 {
    affiche 7, "x", i, "=", 7 * j;
    i = i + 1;
}"""

PROGRAMME_JUSTE = PROGRAMME_FAUX.replace("7 * j", "7 * i")


def pause(titre: str) -> None:
    input(f"\n──── {titre}  (Entrée pour continuer) ")


def montrer(nom: str, valeur: object) -> None:
    print(f"\n{nom} :")
    print(json.dumps(valeur, ensure_ascii=False, indent=2))


async def demo() -> None:
    serveur = StdioServerParameters(
        command=sys.executable, args=["-m", "serveur_plume"], cwd="."
    )
    print("Je branche « l'IA » sur le serveur MCP de Plume…")
    async with Client(serveur, read_timeout_seconds=30) as client:
        assert client.server_info is not None
        print(f"Connecté au serveur « {client.server_info.name} ».")
        print(f"\nSes instructions pour l'IA :\n  {client.instructions}")

        pause("1. Ce que contient la boîte à outils")
        outils = (await client.list_tools()).tools
        ressources = (await client.list_resources()).resources
        print("Les boutons (outils) :")
        for outil in outils:
            resume = (outil.description or "").splitlines()[0]
            print(f"  - {outil.name} : {resume}")
        print("Les choses à lire (ressources) :")
        for ressource in ressources:
            print(f"  - {ressource.uri}")

        pause("2. L'IA lit les règles de Plume")
        spec = (await client.read_resource("plume://specification")).contents[0]
        texte = getattr(spec, "text", "")
        print("\n".join(texte.splitlines()[:12]))
        print("  […]")

        pause("3. L'IA écrit un programme… avec une faute")
        print(PROGRAMME_FAUX)

        pause("4. Elle appuie sur « check »")
        r = await client.call_tool("check", {"source": PROGRAMME_FAUX})
        montrer("Réponse du serveur", r.structured_content)

        pause("5. Elle corrige (j → i) et revérifie")
        print(PROGRAMME_JUSTE)
        r = await client.call_tool("check", {"source": PROGRAMME_JUSTE})
        montrer("Réponse du serveur", r.structured_content)

        pause("6. Elle appuie sur « run »")
        r = await client.call_tool("run", {"source": PROGRAMME_JUSTE})
        resultat = r.structured_content or {}
        print(f"\nStatut : {resultat.get('statut')}")
        print("Ce que le programme affiche :")
        print(resultat.get("sortie", ""))

        pause("7. Bonus : une boucle infinie ne bloque rien")
        r = await client.call_tool("run", {"source": "tantque vrai { }", "delai": 1.0})
        resultat = r.structured_content or {}
        duree = resultat.get("duree")
        print(f"Statut : {resultat.get('statut')} (arrêtée après {duree} s)")

    print("\nFin de la démo.")


if __name__ == "__main__":
    anyio.run(demo)

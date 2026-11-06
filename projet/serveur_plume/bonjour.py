"""Étape 1 : un premier serveur MCP, sans rapport avec Plume.

``@mcp.tool()`` est un décorateur paramétré : il enregistre la fonction dans
le serveur, puis la rend telle quelle. Le SDK lit la signature et la docstring
pour décrire l'outil à l'IA (nom, description, schéma des paramètres).

Lancement : ``python -m serveur_plume.bonjour`` (il attend un client sur stdin).
"""

from typing import Annotated

from mcp.server.mcpserver import MCPServer
from pydantic import Field

mcp = MCPServer(
    "bonjour",
    instructions="Serveur d'essai : il salue et sait additionner deux entiers.",
)


@mcp.tool()
def saluer(nom: Annotated[str, Field(description="Prénom de la personne")]) -> str:
    """Salue une personne par son prénom."""
    return f"Bonjour, {nom} !"


@mcp.tool()
def additionner(a: int, b: int) -> int:
    """Additionne deux entiers."""
    return a + b


@mcp.tool()
def repeter(
    mot: Annotated[str, Field(description="Le mot à répéter")],
    fois: Annotated[int, Field(description="Nombre de répétitions", ge=1, le=20)] = 2,
) -> str:
    """Répète un mot plusieurs fois, séparé par des espaces."""
    return " ".join([mot] * fois)


if __name__ == "__main__":
    mcp.run()

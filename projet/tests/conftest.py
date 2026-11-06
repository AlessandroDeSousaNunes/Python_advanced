"""Rend importable le paquet du langage (le dossier parent de `tests/`) :
`from plume.etape1_lexer.lexer import tokenize` fonctionne alors dans les tests."""

import sys
from pathlib import Path

import pytest


@pytest.fixture
def anyio_backend() -> str:
    """Les tests MCP sont asynchrones : on les fait tourner avec asyncio."""
    return "asyncio"


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Et le module `outils` des tests eux-mêmes.
sys.path.insert(0, str(Path(__file__).resolve().parent))

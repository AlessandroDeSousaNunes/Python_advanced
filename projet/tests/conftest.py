"""Rend importable le paquet du langage (le dossier parent de `tests/`) :
`from plume.lexer import tokenize` fonctionne alors dans les tests."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Et le module `outils` des tests eux-mêmes.
sys.path.insert(0, str(Path(__file__).resolve().parent))

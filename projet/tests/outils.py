"""Outils partagés par les tests."""

from pathlib import Path

PROJET = Path(__file__).resolve().parent.parent
EXEMPLES = sorted((PROJET / "exemples").glob("*.plume"))


def lire(chemin: Path) -> str:
    return chemin.read_text(encoding="utf-8")


def attendu(exemple: Path) -> str:
    return lire(exemple.with_suffix(".attendu"))

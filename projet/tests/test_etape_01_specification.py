from outils import EXEMPLES, PROJET


def test_au_moins_cinq_exemples():
    assert len(EXEMPLES) >= 5


def test_chaque_exemple_a_sa_sortie_attendue():
    for exemple in EXEMPLES:
        assert exemple.with_suffix(".attendu").is_file(), exemple.name


def test_la_specification_existe():
    assert (PROJET / "specification.md").is_file()

import dataclasses

import pytest
from plume.erreurs import Position
from plume.etape2_parser.noeuds import (
    Affiche,
    Binaire,
    Entier,
    Programme,
    Si,
    Variable,
    afficher_arbre,
)


def test_noeuds_immuables():
    noeud = Entier(1)
    with pytest.raises(dataclasses.FrozenInstanceError):
        noeud.valeur = 2  # type: ignore[misc]


def test_position_ignoree_dans_l_egalite_et_le_repr():
    a = Binaire("+", Entier(1), Variable("x"), pos=Position(1, 3))
    b = Binaire("+", Entier(1), Variable("x"), pos=Position(9, 9))
    assert a == b
    assert "pos" not in repr(a)
    assert "Position" not in repr(a)


def test_noeud_sans_position():
    assert Variable("x").pos == Position(0, 0)


def test_afficher_arbre():
    arbre = Programme(
        (Si(Variable("ok"), (Affiche((Binaire("*", Entier(2), Entier(3)),)),)),)
    )
    assert afficher_arbre(arbre) == "\n".join(
        [
            "Programme",
            "  instructions:",
            "    Si",
            "      condition: Variable",
            "        nom: 'ok'",
            "      alors:",
            "        Affiche",
            "          valeurs:",
            "            Binaire",
            "              operateur: '*'",
            "              gauche: Entier",
            "                valeur: 2",
            "              droite: Entier",
            "                valeur: 3",
            "      sinon: None",
        ]
    )


def test_afficher_arbre_tuple_vide():
    assert afficher_arbre(Programme(())) == "Programme\n  instructions: ()"


def test_asdict_fonctionne():
    sans_position = {"ligne": 0, "colonne": 0}
    assert dataclasses.asdict(Binaire("-", Entier(1), Entier(2))) == {
        "operateur": "-",
        "gauche": {"valeur": 1, "pos": sans_position},
        "droite": {"valeur": 2, "pos": sans_position},
        "pos": sans_position,
    }

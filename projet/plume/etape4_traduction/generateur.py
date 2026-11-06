"""La génération de Python.

Quatre précautions :

1. chaque expression imbriquée est mise entre parenthèses, pour que les
   priorités de Python ne changent jamais le sens (``a < b < c``) ;
2. les noms qui gênent en Python (``print``, ``class``, ``len``…) sont
   renommés ``_v_print``… ; un nom Plume ne commence jamais par ``_`` ;
3. ``affiche`` devient un simple ``print``. Seule une valeur qui peut être un
   booléen ou rien passe par ``_texte`` (une petite fonction du prélude), pour
   afficher ``vrai`` / ``faux`` / ``rien`` au lieu de ``True`` / ``False`` /
   ``None``. Le fichier généré reste lançable sans Plume ;
4. une fonction qui modifie une globale commence par ``global``.

En bref : on parcourt l'arbre et, pour chaque nœud, on écrit le Python
équivalent avec ``match`` / ``case`` : un ``Si`` devient ``if``, un
``TantQue`` devient ``while``… Le résultat est du TEXTE, que Python exécutera
ensuite. ``assert_never`` dans le dernier ``case`` fait vérifier par mypy
qu'aucune sorte de nœud n'a été oubliée.
"""

import builtins
import keyword
from typing import assert_never

from plume.etape2_parser.noeuds import (
    Affectation,
    Affiche,
    Appel,
    Binaire,
    Booleen,
    Declaration,
    Entier,
    Expr,
    ExprInstr,
    Fonction,
    Instr,
    Programme,
    Retourne,
    Si,
    TantQue,
    Texte,
    Unaire,
    Variable,
)
from plume.etape3_analyse.semantique import Analyse
from plume.etape4_traduction.backend import Sortie
from plume.etape4_traduction.emetteur import Emetteur

PRELUDE = """\
def _texte(valeur):
    if valeur is True:
        return "vrai"
    if valeur is False:
        return "faux"
    if valeur is None:
        return "rien"
    return str(valeur)

"""

#: Les opérateurs Plume et leur équivalent Python.
OPERATEURS = {
    "ou": "or",
    "et": "and",
    "==": "==",
    "!=": "!=",
    "<": "<",
    "<=": "<=",
    ">": ">",
    ">=": ">=",
    "+": "+",
    "-": "-",
    "*": "*",
    "/": "//",  # division entière
    "%": "%",
}

#: Les fonctions prédéfinies et leur nom dans le prélude.
PREDEFINIES_PYTHON = {"texte": "_texte"}

NOMS_RESERVES = (
    frozenset(keyword.kwlist) | frozenset(keyword.softkwlist) | frozenset(dir(builtins))
)


def nom_python(nom: str) -> str:
    """Le nom à utiliser en Python pour un nom Plume."""
    return f"_v_{nom}" if nom in NOMS_RESERVES else nom


#: Les calculs qui donnent toujours un nombre ou un texte, jamais vrai/faux/rien.
CALCULS = frozenset({"+", "-", "*", "/", "%"})


def jamais_booleen(expr: Expr) -> bool:
    """Vrai si ``expr`` donne sûrement un nombre ou un texte. Alors ``print``
    l'affiche déjà comme Plume, sans passer par ``_texte``."""
    match expr:
        case Entier() | Texte():
            return True
        case Binaire(operateur, _, _):
            return operateur in CALCULS
        case Unaire("-", _):
            return True
        case Appel("texte", _):
            return True
        case _:
            return False


class GenerateurPython:
    nom = "python"
    extension = ".py"
    executable = True

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie:
        self.analyse = analyse
        self.e = Emetteur()
        for ligne in PRELUDE.splitlines():
            self.e.ligne(ligne)
        for instr in programme.instructions:
            self.instruction(instr)
        return Sortie(self.e.texte(), dict(self.e.correspondances))

    def bloc(self, instructions: tuple[Instr, ...]) -> None:
        with self.e.bloc():
            for instr in instructions:
                self.instruction(instr)

    def instruction(self, instr: Instr) -> None:
        e = self.e
        # « depuis » note que les lignes écrites ici viennent de cette ligne
        # Plume : en cas de plantage, on saura quelle ligne montrer.
        with e.depuis(instr.pos):
            match instr:
                case Declaration(nom, valeur) | Affectation(nom, valeur):
                    e.ligne(f"{nom_python(nom)} = {self.expr(valeur)}")
                case Affiche(valeurs):
                    # affiche a, b;  devient  print(a, b)  : print sépare déjà
                    # les valeurs par une espace, comme Plume.
                    morceaux = ", ".join(self.affichable(v) for v in valeurs)
                    e.ligne(f"print({morceaux})")
                case Si(condition, alors, sinon):
                    e.ligne(f"if {self.expr(condition)}:")
                    self.bloc(alors)
                    if sinon is not None:
                        e.ligne("else:")
                        self.bloc(sinon)
                case TantQue(condition, corps):
                    e.ligne(f"while {self.expr(condition)}:")
                    self.bloc(corps)
                case Fonction(nom, parametres, corps):
                    params = ", ".join(nom_python(p) for p in parametres)
                    e.ligne(f"def {nom_python(nom)}({params}):")
                    with e.bloc():
                        globales = self.analyse.globales_modifiees.get(nom, frozenset())
                        if globales:
                            noms = ", ".join(sorted(nom_python(g) for g in globales))
                            e.ligne(f"global {noms}")
                        for sous_instr in corps:
                            self.instruction(sous_instr)
                case Retourne(valeur):
                    e.ligne(
                        "return" if valeur is None else f"return {self.expr(valeur)}"
                    )
                case ExprInstr(expression):
                    e.ligne(self.expr(expression))
                case _:
                    assert_never(instr)

    def affichable(self, expr: Expr) -> str:
        """Une valeur à donner à ``print``. Si elle peut être vrai, faux ou
        rien, on l'entoure de ``_texte(...)`` pour l'afficher en français."""
        code = self.expr(expr)
        return code if jamais_booleen(expr) else f"_texte({code})"

    def expr(self, expr: Expr) -> str:
        # Une expression devient un morceau de texte Python. Chaque calcul est
        # entouré de parenthèses : (1 + (2 * 3)). Python ne peut donc pas le
        # lire dans un autre ordre que Plume.
        match expr:
            case Entier(valeur):
                return str(valeur)
            case Texte(valeur):
                return repr(valeur)  # repr ajoute les guillemets : 'salut'
            case Booleen(valeur):
                return "True" if valeur else "False"
            case Variable(nom):
                return nom_python(nom)
            case Unaire("non", operande):
                return f"(not {self.expr(operande)})"
            case Unaire(_, operande):
                return f"(-{self.expr(operande)})"
            case Binaire(operateur, gauche, droite):
                op = OPERATEURS[operateur]
                return f"({self.expr(gauche)} {op} {self.expr(droite)})"
            case Appel(fonction, arguments):
                nom = PREDEFINIES_PYTHON.get(fonction, nom_python(fonction))
                return f"{nom}({', '.join(self.expr(a) for a in arguments)})"
            case _:
                assert_never(expr)

"""Le formateur : réécrit un programme Plume dans une présentation canonique.

Indentation de quatre espaces, espaces autour des opérateurs et parenthèses
minimales : seulement celles qui changent le sens. Les commentaires ne sont
pas conservés.

C'est un deuxième « backend » : comme le générateur Python, il reçoit l'arbre,
mais il le réécrit en Plume au lieu de le traduire en Python. Il a la même
forme (nom, extension, executable, generer), donc le compilateur l'utilise
sans rien savoir de lui : c'est le principe ouvert/fermé (chapitre 5).
"""

from typing import assert_never

from plume.backend import Sortie
from plume.emetteur import Emetteur
from plume.noeuds import (
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
from plume.parser import APPEL, COMPARAISON, ET, MOINS_UNAIRE, NON, OU, PRODUIT, SOMME
from plume.semantique import Analyse

PRECEDENCES = {
    "ou": OU,
    "et": ET,
    **dict.fromkeys(("==", "!=", "<", "<=", ">", ">="), COMPARAISON),
    **dict.fromkeys(("+", "-"), SOMME),
    **dict.fromkeys(("*", "/", "%"), PRODUIT),
}


def precedence(expr: Expr) -> int:
    match expr:
        case Binaire(operateur, _, _):
            return PRECEDENCES[operateur]
        case Unaire("non", _):
            return NON
        case Unaire(_, _):
            return MOINS_UNAIRE
        case _:
            return APPEL + 1  # littéraux, variables, appels : rien à protéger


def texte_plume(valeur: str) -> str:
    """Un littéral texte, avec ses guillemets et ses échappements."""
    echappe = (
        valeur.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return f'"{echappe}"'


def entre_parentheses(texte: str, condition: bool) -> str:
    return f"({texte})" if condition else texte


class Formateur:
    nom = "formateur"
    extension = ".plume"
    executable = False

    def generer(self, programme: Programme, analyse: Analyse) -> Sortie:
        e = Emetteur()
        instructions = programme.instructions
        for i, instr in enumerate(instructions):
            self.instruction(instr, e)
            # Une ligne vide après chaque fonction, pour aérer.
            if isinstance(instr, Fonction) and i < len(instructions) - 1:
                e.ligne()
        return Sortie(e.texte())

    def bloc(self, instructions: tuple[Instr, ...], e: Emetteur) -> None:
        with e.bloc(vide=None):
            for instr in instructions:
                self.instruction(instr, e)

    def instruction(self, instr: Instr, e: Emetteur) -> None:
        match instr:
            case Declaration(nom, valeur):
                e.ligne(f"soit {nom} = {self.expr(valeur)};")
            case Affectation(nom, valeur):
                e.ligne(f"{nom} = {self.expr(valeur)};")
            case Affiche(valeurs):
                e.ligne(f"affiche {', '.join(self.expr(v) for v in valeurs)};")
            case Si():
                self.si(instr, e)
            case TantQue(condition, corps):
                e.ligne(f"tantque {self.expr(condition)} {{")
                self.bloc(corps, e)
                e.ligne("}")
            case Fonction(nom, parametres, corps):
                e.ligne(f"fonction {nom}({', '.join(parametres)}) {{")
                self.bloc(corps, e)
                e.ligne("}")
            case Retourne(valeur):
                if valeur is None:
                    e.ligne("retourne;")
                else:
                    e.ligne(f"retourne {self.expr(valeur)};")
            case ExprInstr(expression):
                e.ligne(f"{self.expr(expression)};")
            case _:
                assert_never(instr)

    def si(self, si: Si, e: Emetteur) -> None:
        # « sinon { si ... } » s'écrit « sinon si ... » : même arbre.
        entete = f"si {self.expr(si.condition)} {{"
        while True:
            e.ligne(entete)
            self.bloc(si.alors, e)
            sinon = si.sinon
            if sinon is None:
                e.ligne("}")
                return
            if len(sinon) == 1 and isinstance(sinon[0], Si):
                si = sinon[0]
                entete = f"}} sinon si {self.expr(si.condition)} {{"
                continue
            e.ligne("} sinon {")
            self.bloc(sinon, e)
            e.ligne("}")
            return

    def expr(self, expr: Expr) -> str:
        match expr:
            case Entier(valeur):
                return str(valeur)
            case Texte(valeur):
                return texte_plume(valeur)
            case Booleen(valeur):
                return "vrai" if valeur else "faux"
            case Variable(nom):
                return nom
            case Unaire("non", operande):
                # « non » porte sur tout ce qui est plus prioritaire que « et ».
                interieur = self.expr(operande)
                return "non " + entre_parentheses(interieur, precedence(operande) <= ET)
            case Unaire(_, operande):
                interieur = self.expr(operande)
                interieur = entre_parentheses(
                    interieur, precedence(operande) < MOINS_UNAIRE
                )
                return (
                    "- " + interieur if interieur.startswith("-") else "-" + interieur
                )
            case Binaire(operateur, gauche, droite):
                p = PRECEDENCES[operateur]
                return (
                    f"{self.operande(gauche, p, a_droite=False)} {operateur} "
                    f"{self.operande(droite, p, a_droite=True)}"
                )
            case Appel(fonction, arguments):
                return f"{fonction}({', '.join(self.expr(a) for a in arguments)})"
            case _:
                assert_never(expr)

    def operande(self, expr: Expr, p: int, *, a_droite: bool) -> str:
        """Un opérande de binaire, entre parenthèses seulement si besoin."""
        q = precedence(expr)
        # Associatif à gauche : à droite, une précédence égale doit être protégée.
        besoin = q < p or (a_droite and q == p)
        # « non x » avale toute comparaison ou calcul qui le suit : on le
        # protège dès que l'opérateur est plus prioritaire que « et ».
        if isinstance(expr, Unaire) and expr.operateur == "non" and p > ET:
            besoin = True
        return entre_parentheses(self.expr(expr), besoin)

"""L'analyse sémantique : vérifie les déclarations et les portées.

Python n'a pas de portée de bloc. Pour que le Python généré garde le sens du
programme Plume, on interdit de redéclarer un nom tant qu'il est visible :
pas de masquage dans un bloc, et pas de locale qui porte le nom d'une
globale. On note aussi les globales que chaque fonction modifie, pour que le
générateur émette ``global``.

En bref : on parcourt l'arbre nœud par nœud, avec une table des NOMS déclarés
(pas de valeurs : on ne fait aucun calcul ici). Pour chaque nom utilisé, on
vérifie qu'il existe ; pour chaque nom déclaré, qu'il n'existe pas déjà.
Toutes les erreurs sont collectées, puis signalées ensemble.

``singledispatchmethod`` (chapitre 2) choisit la bonne méthode selon le TYPE
du nœud : ``self.instruction(noeud)`` appelle la variante écrite pour
``Declaration`` si c'est une déclaration, celle pour ``Si`` si c'est un si…
"""

from dataclasses import dataclass
from functools import singledispatchmethod

from plume.erreurs import ErreurPlume, ErreurSemantique, ErreursMultiples, Position
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
from plume.symboles import Genre, Symbole, TableSymboles

#: Les fonctions prédéfinies et leur nombre de paramètres.
PREDEFINIES: dict[str, int] = {"texte": 1}


@dataclass(frozen=True)
class Analyse:
    """Ce dont le générateur a besoin : pour chaque fonction, les variables
    globales qu'elle modifie."""

    globales_modifiees: dict[str, frozenset[str]]


class Analyseur:
    def __init__(self) -> None:
        self.table = TableSymboles()  # les noms déclarés, portée par portée
        self.erreurs: list[ErreurPlume] = []  # toutes les erreurs trouvées
        self.fonction: str | None = None  # la fonction en cours d'analyse
        self.globales: dict[str, set[str]] = {}  # fonction -> globales modifiées
        for nom, nb in PREDEFINIES.items():
            self.table.declarer(Symbole(nom, Genre.PREDEFINIE, nb_parametres=nb))

    def analyser(self, programme: Programme) -> Analyse:
        """Vérifie tout le programme. Lève une seule ``ErreursMultiples`` qui
        contient toutes les erreurs."""
        self.erreurs = []
        for instr in programme.instructions:
            self.instruction(instr)
        if self.erreurs:
            raise ErreursMultiples(self.erreurs)
        return Analyse({f: frozenset(g) for f, g in self.globales.items()})

    # --- Outils ---------------------------------------------------------------

    def erreur(self, message: str, position: Position) -> None:
        self.erreurs.append(ErreurSemantique(message, position))

    def declarer(
        self, nom: str, genre: Genre, position: Position, nb_parametres: int = 0
    ) -> None:
        # La règle centrale de Plume : un nom encore visible ne peut pas être
        # redéclaré. Python n'a pas de portée de bloc : sans cette règle, le
        # Python généré mélangerait deux variables de même nom.
        existant = self.table.chercher(nom)
        if existant is not None:
            if existant.genre is Genre.PREDEFINIE:
                self.erreur(f"« {nom} » est une fonction prédéfinie", position)
            else:
                self.erreur(
                    f"« {nom} » est déjà déclaré ({existant.position})", position
                )
            return
        symbole = Symbole(nom, genre, position, nb_parametres, self.fonction)
        self.table.declarer(symbole)

    def corps(self, instructions: tuple[Instr, ...]) -> None:
        """Un bloc : une nouvelle portée."""
        with self.table.portee():
            for instr in instructions:
                self.instruction(instr)

    # --- Instructions ---------------------------------------------------------

    @singledispatchmethod
    def instruction(self, instr: Instr) -> None:
        raise TypeError(f"instruction inconnue : {instr!r}")

    @instruction.register
    def _(self, instr: Declaration) -> None:
        # La valeur d'abord : « soit x = x; » utilise un x inconnu.
        self.expression(instr.valeur)
        self.declarer(instr.nom, Genre.VARIABLE, instr.pos)

    @instruction.register
    def _(self, instr: Affectation) -> None:
        self.expression(instr.valeur)
        symbole = self.table.chercher(instr.nom)
        if symbole is None:
            self.erreur(f"variable inconnue « {instr.nom} »", instr.pos)
        elif symbole.est_fonction:
            self.erreur(
                f"on ne peut pas affecter à la fonction « {instr.nom} »", instr.pos
            )
        elif self.fonction is not None and symbole.fonction is None:
            # On est dans une fonction, et la variable vient du niveau
            # principal : il faudra « global » en Python, on le note.
            self.globales[self.fonction].add(instr.nom)

    @instruction.register
    def _(self, instr: Affiche) -> None:
        for valeur in instr.valeurs:
            self.expression(valeur)

    @instruction.register
    def _(self, instr: Si) -> None:
        self.expression(instr.condition)
        self.corps(instr.alors)
        if instr.sinon is not None:
            self.corps(instr.sinon)

    @instruction.register
    def _(self, instr: TantQue) -> None:
        self.expression(instr.condition)
        self.corps(instr.corps)

    @instruction.register
    def _(self, instr: Fonction) -> None:
        if self.fonction is not None or self.table.profondeur > 1:
            self.erreur(
                "une fonction ne peut être déclarée qu'au niveau principal", instr.pos
            )
            return
        # Déclarée avant son corps : elle peut s'appeler elle-même.
        self.declarer(instr.nom, Genre.FONCTION, instr.pos, len(instr.parametres))
        self.fonction = instr.nom
        self.globales[instr.nom] = set()
        try:
            with self.table.portee():
                for parametre in instr.parametres:
                    self.declarer(parametre, Genre.PARAMETRE, instr.pos)
                for sous_instr in instr.corps:
                    self.instruction(sous_instr)
        finally:
            self.fonction = None

    @instruction.register
    def _(self, instr: Retourne) -> None:
        if self.fonction is None:
            self.erreur("« retourne » en dehors d'une fonction", instr.pos)
        if instr.valeur is not None:
            self.expression(instr.valeur)

    @instruction.register
    def _(self, instr: ExprInstr) -> None:
        self.expression(instr.expression)

    # --- Expressions ----------------------------------------------------------

    @singledispatchmethod
    def expression(self, expr: Expr) -> None:
        raise TypeError(f"expression inconnue : {expr!r}")

    @expression.register
    def _(self, expr: Entier | Texte | Booleen) -> None:
        pass

    @expression.register
    def _(self, expr: Variable) -> None:
        symbole = self.table.chercher(expr.nom)
        if symbole is None:
            self.erreur(f"variable inconnue « {expr.nom} »", expr.pos)
        elif symbole.est_fonction:
            self.erreur(
                f"« {expr.nom} » est une fonction : appelez-la avec {expr.nom}(...)",
                expr.pos,
            )

    @expression.register
    def _(self, expr: Unaire) -> None:
        self.expression(expr.operande)

    @expression.register
    def _(self, expr: Binaire) -> None:
        self.expression(expr.gauche)
        self.expression(expr.droite)

    @expression.register
    def _(self, expr: Appel) -> None:
        symbole = self.table.chercher(expr.fonction)
        if symbole is None:
            self.erreur(f"fonction inconnue « {expr.fonction} »", expr.pos)
        elif not symbole.est_fonction:
            self.erreur(f"« {expr.fonction} » n'est pas une fonction", expr.pos)
        elif len(expr.arguments) != symbole.nb_parametres:
            self.erreur(
                f"« {expr.fonction} » attend {symbole.nb_parametres} argument(s), "
                f"{len(expr.arguments)} donné(s)",
                expr.pos,
            )
        for argument in expr.arguments:
            self.expression(argument)


def analyser(programme: Programme) -> Analyse:
    """Analyse un programme complet avec un analyseur neuf."""
    return Analyseur().analyser(programme)

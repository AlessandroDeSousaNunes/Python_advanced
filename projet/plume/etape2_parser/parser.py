"""Le parser : transforme les tokens en arbre (AST).

Les expressions sont analysées par la méthode de Pratt : chaque type de token
a une règle « préfixe » (il commence une expression) et/ou une règle
« infixe » (il suit une expression déjà lue), avec une précédence. Les
décorateurs ``prefixe`` et ``infixe`` remplissent les deux tables.

En bref : le parser lit les tokens un par un et les ASSEMBLE en arbre.

- Pour une instruction, il regarde le PREMIER token pour choisir un modèle
  (``soit`` = déclaration, ``si`` = condition…), puis il remplit les trous
  du modèle dans l'ordre avec ``attend`` (« ici, il me faut un nom »).
- Pour un calcul, chaque opérateur a une FORCE (sa précédence) : les plus
  forts prennent leurs voisins en premier, donc ``1 + 2 * 3`` donne
  ``1 + (2 * 3)``.
- En cas d'erreur, il la note et saute à l'instruction suivante, pour pouvoir
  signaler toutes les erreurs d'un coup.
"""

from collections.abc import Callable, Iterable

from plume.erreurs import (
    ErreurLexicale,
    ErreurPlume,
    ErreursMultiples,
    ErreurSyntaxe,
)
from plume.etape1_lexer.flux import Flux
from plume.etape1_lexer.lexer import tokenize
from plume.etape1_lexer.tokens import Token, TokenKind
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

T = TokenKind

# Précédences, de la plus faible à la plus forte (voir la spécification).
OU, ET, NON, COMPARAISON, SOMME, PRODUIT, MOINS_UNAIRE, APPEL = range(1, 9)

RegleePrefixe = Callable[["Parser", Token], Expr]
RegleInfixe = Callable[["Parser", Expr, Token], Expr]

# Les deux tables de Pratt, remplies par les décorateurs plus bas :
# - PREFIXES : « ce token peut COMMENCER une expression, voici comment » ;
# - INFIXES : « ce token peut PROLONGER une expression, avec cette force ».
PREFIXES: dict[TokenKind, RegleePrefixe] = {}
INFIXES: dict[TokenKind, tuple[int, RegleInfixe]] = {}

#: Les mots-clés qui commencent une instruction : on s'y resynchronise.
DEBUTS_INSTRUCTION = frozenset(
    {T.SOIT, T.SI, T.TANTQUE, T.FONCTION, T.RETOURNE, T.AFFICHE}
)


# Un décorateur paramétré (chapitre 2) : ``@prefixe(T.ENTIER)`` au-dessus d'une
# méthode l'inscrit dans la table PREFIXES, puis renvoie la méthode inchangée.
def prefixe(*kinds: TokenKind) -> Callable[[RegleePrefixe], RegleePrefixe]:
    """Enregistre une règle préfixe pour chacun des ``kinds``."""

    def decorateur(regle: RegleePrefixe) -> RegleePrefixe:
        for kind in kinds:
            PREFIXES[kind] = regle
        return regle

    return decorateur


def infixe(*kinds: TokenKind, precedence: int) -> Callable[[RegleInfixe], RegleInfixe]:
    """Enregistre une règle infixe de précédence ``precedence``."""

    def decorateur(regle: RegleInfixe) -> RegleInfixe:
        for kind in kinds:
            INFIXES[kind] = (precedence, regle)
        return regle

    return decorateur


def decrire(jeton: Token) -> str:
    """Le token tel qu'on le cite dans un message d'erreur."""
    match jeton.kind:
        case T.FIN:
            return "la fin du fichier"
        case T.IDENT:
            return f"'{jeton.lexeme}'"
        case T.ENTIER:
            return jeton.lexeme
        case T.TEXTE:
            return f'"{jeton.lexeme}"'
        case _:
            return str(jeton.kind)


class Parser:
    def __init__(self, tokens: Iterable[Token]) -> None:
        self.flux = Flux(tokens)  # les tokens, avec la possibilité de regarder devant
        self.erreurs: list[ErreurPlume] = []  # les erreurs trouvées jusqu'ici
        self.precedent: Token | None = None  # le dernier token consommé

    # --- Accès aux tokens -----------------------------------------------------

    def regarde(self, decalage: int = 0) -> Token:
        jeton = self.flux.regarde(decalage)
        assert jeton is not None, "le lexer produit toujours FIN en dernier"
        return jeton

    def avance(self) -> Token:
        """Consomme le token courant. ``FIN`` n'est jamais consommé."""
        jeton = self.regarde()
        if jeton.kind is not T.FIN:
            self.flux.avance()
            self.precedent = jeton
        return jeton

    def verifie(self, kind: TokenKind) -> bool:
        return self.regarde().kind is kind

    def accepte(self, kind: TokenKind) -> Token | None:
        """Consomme le token s'il est du bon type, sinon ne fait rien."""
        return self.avance() if self.verifie(kind) else None

    def attend(self, kind: TokenKind, contexte: str) -> Token:
        """Consomme un token du type attendu, ou lève une erreur de syntaxe."""
        if self.verifie(kind):
            return self.avance()
        trouve = self.regarde()
        position = trouve.position
        # Un ';' oublié se signale juste après le token précédent.
        if kind is T.POINT_VIRGULE and self.precedent is not None:
            position = self.precedent.fin
        raise ErreurSyntaxe(
            f"{kind} attendu {contexte}, trouvé {decrire(trouve)}", position
        )

    # --- Expressions (Pratt) --------------------------------------------------

    def expression(self, precedence: int = 0) -> Expr:
        """Lit une expression. ``precedence`` : on ne garde que les opérateurs
        PLUS FORTS que ce niveau ; les autres sont laissés à l'appelant.

        Sur ``1 + 2 * 3`` : on lit 1 ; on voit ``+`` (force 5), il lit sa
        droite avec expression(5) ; celle-ci lit 2, voit ``*`` (force 6 > 5)
        et le garde : 2 * 3. Le ``+`` reçoit donc ``2 * 3`` comme droite.
        """
        # 1. Le début de l'expression : un nombre, un nom, '(', '-', 'non'…
        jeton = self.regarde()
        regle = PREFIXES.get(jeton.kind)
        if regle is None:
            raise ErreurSyntaxe(
                f"expression attendue, trouvé {decrire(jeton)}", jeton.position
            )
        self.avance()
        gauche = regle(self, jeton)
        # 2. Tant que le token suivant est un opérateur plus fort que notre
        #    niveau, il prend ce qu'on a déjà lu comme opérande gauche.
        while True:
            suivant = self.regarde()
            entree = INFIXES.get(suivant.kind)
            if entree is None or entree[0] <= precedence:
                return gauche
            self.avance()
            gauche = entree[1](self, gauche, suivant)

    @prefixe(T.ENTIER)
    def _entier(self, jeton: Token) -> Expr:
        return Entier(int(jeton.lexeme), pos=jeton.position)

    @prefixe(T.TEXTE)
    def _texte(self, jeton: Token) -> Expr:
        return Texte(jeton.lexeme, pos=jeton.position)

    @prefixe(T.VRAI, T.FAUX)
    def _booleen(self, jeton: Token) -> Expr:
        return Booleen(jeton.kind is T.VRAI, pos=jeton.position)

    @prefixe(T.IDENT)
    def _variable(self, jeton: Token) -> Expr:
        return Variable(jeton.lexeme, pos=jeton.position)

    @prefixe(T.PAR_OUVRANTE)
    def _parentheses(self, jeton: Token) -> Expr:
        interieur = self.expression()
        self.attend(T.PAR_FERMANTE, f"pour fermer la '(' de la {jeton.position}")
        return interieur

    @prefixe(T.MOINS)
    def _moins(self, jeton: Token) -> Expr:
        return Unaire("-", self.expression(MOINS_UNAIRE), pos=jeton.position)

    @prefixe(T.NON)
    def _non(self, jeton: Token) -> Expr:
        return Unaire("non", self.expression(NON), pos=jeton.position)

    @infixe(T.OU, precedence=OU)
    @infixe(T.ET, precedence=ET)
    @infixe(
        T.EGAL_EGAL,
        T.DIFFERENT,
        T.INFERIEUR,
        T.INFERIEUR_EGAL,
        T.SUPERIEUR,
        T.SUPERIEUR_EGAL,
        precedence=COMPARAISON,
    )
    @infixe(T.PLUS, T.MOINS, precedence=SOMME)
    @infixe(T.FOIS, T.DIVISE, T.MODULO, precedence=PRODUIT)
    def _binaire(self, gauche: Expr, jeton: Token) -> Expr:
        # L'opérande droit ne prend que des opérateurs strictement plus
        # prioritaires : c'est ce qui rend l'opérateur associatif à gauche.
        precedence = INFIXES[jeton.kind][0]
        droite = self.expression(precedence)
        return Binaire(jeton.lexeme, gauche, droite, pos=jeton.position)

    @infixe(T.PAR_OUVRANTE, precedence=APPEL)
    def _appel(self, gauche: Expr, jeton: Token) -> Expr:
        if not isinstance(gauche, Variable):
            raise ErreurSyntaxe(
                "seule une fonction nommée peut être appelée", jeton.position
            )
        arguments: list[Expr] = []
        if not self.accepte(T.PAR_FERMANTE):
            arguments.append(self.expression())
            while self.accepte(T.VIRGULE):
                arguments.append(self.expression())
            self.attend(T.PAR_FERMANTE, f"pour fermer l'appel de '{gauche.nom}'")
        return Appel(gauche.nom, tuple(arguments), pos=gauche.pos)

    # --- Instructions ---------------------------------------------------------

    def programme(self) -> Programme:
        instructions: list[Instr] = []
        while not self.verifie(T.FIN):
            if self.verifie(T.ACC_FERMANTE):
                jeton = self.avance()
                self.erreurs.append(
                    ErreurSyntaxe("'}' en trop : aucun bloc à fermer", jeton.position)
                )
                continue
            self._proteger(instructions)
        return Programme(tuple(instructions))

    def bloc(self) -> tuple[Instr, ...]:
        ouvrante = self.attend(T.ACC_OUVRANTE, "pour ouvrir le bloc")
        instructions: list[Instr] = []
        while not self.verifie(T.ACC_FERMANTE) and not self.verifie(T.FIN):
            self._proteger(instructions)
        self.attend(
            T.ACC_FERMANTE,
            f"pour fermer le bloc ouvert ligne {ouvrante.position.ligne}",
        )
        return tuple(instructions)

    def _proteger(self, instructions: list[Instr]) -> None:
        """Analyse une instruction ; en cas d'erreur de syntaxe, la note et
        saute au début probable de l'instruction suivante."""
        depart = self.regarde()
        try:
            instructions.append(self.instruction())
        except ErreurSyntaxe as erreur:
            self.erreurs.append(erreur)
            self._synchroniser(depart)

    def _synchroniser(self, depart: Token) -> None:
        # Après une erreur : on saute des tokens jusqu'à un endroit où une
        # nouvelle instruction commence sûrement (après un « ; », ou devant un
        # mot-clé comme « soit »). Le parser peut alors continuer.
        if self.regarde() is depart:  # rien n'a été consommé : on avance
            self.avance()
        while not self.verifie(T.FIN):
            jeton = self.regarde()
            if jeton.kind is T.POINT_VIRGULE:
                self.avance()
                return
            if jeton.kind in DEBUTS_INSTRUCTION or jeton.kind is T.ACC_FERMANTE:
                return
            self.avance()

    def instruction(self) -> Instr:
        # Le PREMIER token décide du modèle à suivre.
        match self.regarde().kind:
            case T.SOIT:
                return self.declaration()
            case T.AFFICHE:
                return self.affiche()
            case T.SI:
                return self.si()
            case T.TANTQUE:
                return self.tantque()
            case T.FONCTION:
                return self.fonction()
            case T.RETOURNE:
                return self.retourne()
            case _:
                return self.affectation_ou_expression()

    def _fin_instruction(self) -> None:
        self.attend(T.POINT_VIRGULE, "à la fin de l'instruction")

    def declaration(self) -> Declaration:
        # Le modèle : soit [nom] = [expression] ;
        mot = self.avance()  # le mot-clé « soit »
        nom = self.attend(T.IDENT, "après 'soit'")  # il faut un nom
        self.attend(T.EGAL, f"après 'soit {nom.lexeme}'")  # puis un « = »
        valeur = self.expression()  # puis un calcul
        self._fin_instruction()  # puis un « ; »
        return Declaration(nom.lexeme, valeur, pos=mot.position)

    def affectation_ou_expression(self) -> Affectation | ExprInstr:
        # Une affectation commence comme une expression : on lit l'expression,
        # puis on vérifie que c'est une cible valide si un '=' suit.
        expression = self.expression()
        if self.verifie(T.EGAL):
            egal = self.avance()
            if not isinstance(expression, Variable):
                raise ErreurSyntaxe(
                    "on ne peut affecter qu'à une variable", egal.position
                )
            valeur = self.expression()
            self._fin_instruction()
            return Affectation(expression.nom, valeur, pos=expression.pos)
        self._fin_instruction()
        return ExprInstr(expression, pos=expression.pos)

    def affiche(self) -> Affiche:
        mot = self.avance()
        valeurs = [self.expression()]
        while self.accepte(T.VIRGULE):
            valeurs.append(self.expression())
        self._fin_instruction()
        return Affiche(tuple(valeurs), pos=mot.position)

    def si(self) -> Si:
        mot = self.avance()
        condition = self.expression()
        alors = self.bloc()
        sinon: tuple[Instr, ...] | None = None
        if self.accepte(T.SINON):
            sinon = (self.si(),) if self.verifie(T.SI) else self.bloc()
        return Si(condition, alors, sinon, pos=mot.position)

    def tantque(self) -> TantQue:
        mot = self.avance()
        condition = self.expression()
        return TantQue(condition, self.bloc(), pos=mot.position)

    def fonction(self) -> Fonction:
        mot = self.avance()
        nom = self.attend(T.IDENT, "après 'fonction'")
        self.attend(T.PAR_OUVRANTE, f"après 'fonction {nom.lexeme}'")
        parametres: list[str] = []
        if not self.accepte(T.PAR_FERMANTE):
            parametres.append(self.attend(T.IDENT, "comme paramètre").lexeme)
            while self.accepte(T.VIRGULE):
                parametres.append(self.attend(T.IDENT, "comme paramètre").lexeme)
            self.attend(T.PAR_FERMANTE, "pour fermer la liste des paramètres")
        corps = self.bloc()
        return Fonction(nom.lexeme, tuple(parametres), corps, pos=mot.position)

    def retourne(self) -> Retourne:
        mot = self.avance()
        valeur = None if self.verifie(T.POINT_VIRGULE) else self.expression()
        self._fin_instruction()
        return Retourne(valeur, pos=mot.position)


# --- Points d'entrée ----------------------------------------------------------


def parse_expression(source: str) -> Expr:
    """Analyse une expression seule, sans rien derrière."""
    parser = Parser(tokenize(source))
    expression = parser.expression()
    parser.attend(T.FIN, "après l'expression")
    return expression


def parse(source: str) -> Programme:
    """Analyse un programme entier. S'il y a des erreurs, lève une seule
    ``ErreursMultiples`` qui les contient toutes."""
    parser = Parser(tokenize(source))
    programme = Programme(())
    try:
        programme = parser.programme()
    except ErreurLexicale as erreur:  # le lexer ne peut pas reprendre
        parser.erreurs.append(erreur)
    if parser.erreurs:
        raise ErreursMultiples(parser.erreurs) from parser.erreurs[0]
    return programme

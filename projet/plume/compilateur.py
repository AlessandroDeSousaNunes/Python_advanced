"""La façade du compilateur : le seul module que la CLI, le REPL et le serveur
MCP utilisent. Plus rien d'autre n'appelle directement le lexer, le parser ou
le générateur.

La chaîne complète, en trois fonctions :

    compiler(source)    texte -> tokens -> arbre -> arbre vérifié
    transpiler(source)  ... -> code Python (du texte)
    executer(source)    ... -> Python exécute ce code, l'affichage apparaît
"""

import traceback
from dataclasses import dataclass

from plume.backend import Backend, Sortie
from plume.erreurs import (
    ErreurBackend,
    ErreurExecution,
    ErreurLexicale,
    ErreurPlume,
    Position,
)
from plume.formateur import Formateur
from plume.generateur import GenerateurPython
from plume.lexer import tokenize
from plume.noeuds import Programme
from plume.parser import parse, parse_expression
from plume.semantique import Analyse, Analyseur
from plume.tokens import TokenKind

#: Le nom de fichier du code généré : il permet de reconnaître ses lignes dans
#: un traceback.
NOM_FICHIER = "<plume>"

#: Les backends disponibles, par nom.
BACKENDS: dict[str, Backend] = {b.nom: b for b in (GenerateurPython(), Formateur())}

#: Les erreurs Python et leur traduction pour l'utilisateur.
MESSAGES_EXECUTION: dict[type[BaseException], str] = {
    ZeroDivisionError: "division par zéro",
    RecursionError: "trop d'appels imbriqués (récursion sans fin ?)",
    TypeError: "opération impossible entre ces types de valeurs",
}


@dataclass(frozen=True)
class Compilation:
    programme: Programme
    analyse: Analyse


def choisir_backend(nom: str) -> Backend:
    try:
        return BACKENDS[nom]
    except KeyError:
        disponibles = ", ".join(sorted(BACKENDS))
        raise ErreurBackend(
            f"backend inconnu « {nom} » (disponibles : {disponibles})"
        ) from None


def compiler(source: str) -> Compilation:
    """Analyse syntaxique puis sémantique. Lève ``ErreursMultiples``."""
    programme = parse(source)  # lexer + parser : texte -> arbre
    return Compilation(programme, Analyseur().analyser(programme))  # vérifications


def transpiler(source: str, backend: str = "python") -> Sortie:
    """Le code produit par ``backend``, et la correspondance de ses lignes."""
    choix = choisir_backend(backend)
    compilation = compiler(source)
    return choix.generer(compilation.programme, compilation.analyse)


def executer(source: str, backend: str = "python") -> None:
    """Compile et exécute ``source`` ; l'affichage va sur ``sys.stdout``."""
    choix = choisir_backend(backend)
    if not choix.executable:
        raise ErreurBackend(
            f"le backend « {backend} » ne produit pas de code exécutable"
        )
    compilation = compiler(source)
    lancer(choix.generer(compilation.programme, compilation.analyse), {})


def lancer(sortie: Sortie, espace: dict[str, object]) -> None:
    """Exécute le code produit dans ``espace``. Une erreur Python devient une
    ``ErreurExecution`` placée à la ligne Plume fautive."""
    # À partir d'ici, c'est Python qui travaille : compile() prépare le texte
    # Python, exec() l'exécute. Les variables du programme sont rangées dans
    # le dictionnaire ``espace``.
    code = compile(sortie.code, NOM_FICHIER, "exec")
    espace.setdefault("__name__", "__main__")
    try:
        exec(code, espace)
    except Exception as exc:
        raise traduire(exc, sortie) from exc


def traduire(exc: Exception, sortie: Sortie) -> ErreurExecution:
    """Cherche, de la frame la plus profonde à la moins profonde, la première
    ligne du code généré qui vient d'une ligne Plume."""
    position: Position | None = None
    for frame in reversed(traceback.extract_tb(exc.__traceback__)):
        if frame.filename == NOM_FICHIER and frame.lineno in sortie.correspondances:
            position = sortie.correspondances[frame.lineno]
            break
    message = next(
        (m for t, m in MESSAGES_EXECUTION.items() if isinstance(exc, t)),
        f"{type(exc).__name__} : {exc}",
    )
    return ErreurExecution(message, position)


# --- Pour le REPL -------------------------------------------------------------


def est_expression(source: str) -> bool:
    """Vrai si ``source`` est une expression seule (sans ``;``)."""
    try:
        parse_expression(source)
    except ErreurPlume:
        return False
    return True


def est_incomplet(source: str) -> bool:
    """Vrai si un bloc est encore ouvert : le REPL attend la suite."""
    profondeur = 0
    try:
        for jeton in tokenize(source):
            if jeton.kind is TokenKind.ACC_OUVRANTE:
                profondeur += 1
            elif jeton.kind is TokenKind.ACC_FERMANTE:
                profondeur -= 1
    except ErreurLexicale:
        return False
    return profondeur > 0


class Session:
    """Compile et exécute des morceaux de programme successifs en gardant ce
    qui a été déclaré. Un morceau qui échoue n'efface rien de ce qui précède."""

    def __init__(self) -> None:
        self.analyseur = Analyseur()
        self.espace: dict[str, object] = {}

    def executer(self, source: str) -> None:
        programme = parse(source)
        sauvegarde = self.analyseur.table.instantane()
        try:
            analyse = self.analyseur.analyser(programme)
            lancer(GenerateurPython().generer(programme, analyse), self.espace)
        except ErreurPlume:
            self.analyseur.table.restaurer(sauvegarde)
            raise

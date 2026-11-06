"""Le serveur MCP de Plume.

Une IA qui ne connaît pas Plume se branche sur ce serveur. Il lui donne :

- des OUTILS qu'elle peut appeler : découper (tokenize), analyser (parse),
  vérifier (check), traduire (transpile), mettre en forme (format), exécuter
  (run) ;
- des RESSOURCES qu'elle peut lire : la spécification et les exemples ;
- des PROMPTS, des modes d'emploi tout prêts : écrire un programme, en corriger un.

Chaque outil est une fine couche autour de la façade
``plume.etape5_execution.compilateur`` : il appelle la façade, puis convertit
le résultat en JSON.
"""

import re
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Annotated, Literal, TypedDict

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from mcp_types import ToolAnnotations
from plume.erreurs import ErreurPlume, ErreursMultiples, formater
from plume.etape1_lexer.tokens import Token
from plume.etape5_execution.compilateur import (
    BACKENDS,
    analyser_syntaxe,
    compiler,
    decouper,
    transpiler,
)
from pydantic import Field

from serveur_plume import bac_a_sable

PROJET = Path(__file__).resolve().parent.parent
SPECIFICATION = PROJET / "specification.md"
EXEMPLES = PROJET / "exemples"

mcp = MCPServer(
    "plume",
    instructions=(
        "Ce serveur sert à écrire des programmes en Plume, un petit langage aux "
        "mots-clés français, traduit en Python. Tu ne connais pas Plume : commence "
        "par lire la resource plume://specification, puis un exemple (liste dans "
        "plume://exemples). Écris ton programme, vérifie-le avec l'outil check, "
        "corrige les erreurs (chacune donne sa ligne et sa colonne), puis exécute-le "
        "avec run."
    ),
)

# Les outils qui ne modifient rien : l'hôte peut les appeler sans demander.
LECTURE_SEULE = ToolAnnotations(
    read_only_hint=True, idempotent_hint=True, open_world_hint=False
)

Source = Annotated[str, Field(description="Code source d'un programme Plume")]


# --- Les formes des réponses (TypedDict) ---------------------------------------


class ErreurJSON(TypedDict):
    genre: str  # "erreur lexicale", "erreur de syntaxe"…
    message: str
    ligne: int | None
    colonne: int | None
    contexte: str  # le message complet, avec la ligne fautive et un ^


class TokenJSON(TypedDict):
    type: str
    texte: str
    ligne: int
    colonne: int


class ResultatTokenize(TypedDict):
    ok: bool
    tokens: list[TokenJSON]
    erreurs: list[ErreurJSON]


class ResultatParse(TypedDict):
    ok: bool
    arbre: dict[str, object] | None
    erreurs: list[ErreurJSON]


class ResultatCheck(TypedDict):
    ok: bool
    erreurs: list[ErreurJSON]


class ResultatTranspile(TypedDict):
    ok: bool
    code: str
    correspondances: dict[str, list[int]] | None  # ligne Python -> [ligne, colonne]
    erreurs: list[ErreurJSON]


class ResultatFormat(TypedDict):
    ok: bool
    code: str
    modifie: bool
    avertissement: str | None
    erreurs: list[ErreurJSON]


Statut = Literal[
    "ok", "erreur_compilation", "erreur_execution", "delai_depasse", "sortie_tronquee"
]


class ResultatRun(TypedDict):
    statut: Statut
    sortie: str
    erreurs: list[ErreurJSON]
    duree: float


# --- Conversions vers JSON ------------------------------------------------------


def erreurs_json(erreur: ErreurPlume, source: str) -> list[ErreurJSON]:
    """Une entrée par erreur (une ErreursMultiples est aplatie)."""
    liste = erreur.erreurs if isinstance(erreur, ErreursMultiples) else [erreur]
    resultat: list[ErreurJSON] = []
    for e in liste:
        pos = e.position
        connue = pos is not None and pos.ligne > 0
        resultat.append(
            {
                "genre": e.genre,
                "message": e.message,
                "ligne": pos.ligne if pos is not None and connue else None,
                "colonne": pos.colonne if pos is not None and connue else None,
                "contexte": formater(e, source, "programme.plume"),
            }
        )
    return resultat


def token_json(jeton: Token) -> TokenJSON:
    return {
        "type": jeton.kind.name,
        "texte": jeton.lexeme,
        "ligne": jeton.position.ligne,
        "colonne": jeton.position.colonne,
    }


def noeud_json(valeur: object) -> object:
    """Convertit un nœud de l'arbre en JSON, avec son type et sa position."""
    if is_dataclass(valeur) and not isinstance(valeur, type):
        resultat: dict[str, object] = {"type": type(valeur).__name__}
        for champ in fields(valeur):
            if champ.name != "pos":
                resultat[champ.name] = noeud_json(getattr(valeur, champ.name))
        pos = getattr(valeur, "pos", None)
        if pos is not None and pos.ligne > 0:
            resultat["ligne"] = pos.ligne
            resultat["colonne"] = pos.colonne
        return resultat
    if isinstance(valeur, tuple):
        return [noeud_json(v) for v in valeur]
    if valeur is None or isinstance(valeur, bool | int | str):
        return valeur
    raise TypeError(f"valeur inattendue dans l'arbre : {valeur!r}")


def contient_un_commentaire(source: str) -> bool:
    """Vrai s'il y a un ``#`` hors d'un texte entre guillemets."""
    for jeton_ou_texte in re.finditer(r'"(?:\\.|[^"\\\n])*"|#', source):
        if jeton_ou_texte.group(0) == "#":
            return True
    return False


# --- Les outils -----------------------------------------------------------------


@mcp.tool(name="tokenize", annotations=LECTURE_SEULE)
def outil_tokenize(source: Source) -> ResultatTokenize:
    """Découpe un programme Plume en tokens (les mots, avec leur type et leur
    position). En cas d'erreur lexicale, renvoie aussi les tokens lus avant."""
    jetons, erreur = decouper(source)
    erreurs = erreurs_json(erreur, source) if erreur is not None else []
    return {
        "ok": erreur is None,
        "tokens": [token_json(j) for j in jetons],
        "erreurs": erreurs,
    }


@mcp.tool(name="parse", annotations=LECTURE_SEULE)
def outil_parse(source: Source) -> ResultatParse:
    """Construit l'arbre syntaxique d'un programme Plume. Ne vérifie que la
    syntaxe, pas le sens : une variable inconnue passe. Pour tout vérifier,
    utilise check."""
    try:
        programme = analyser_syntaxe(source)
    except ErreurPlume as erreur:
        return {"ok": False, "arbre": None, "erreurs": erreurs_json(erreur, source)}
    arbre = noeud_json(programme)
    assert isinstance(arbre, dict)
    return {"ok": True, "arbre": arbre, "erreurs": []}


@mcp.tool(name="check", annotations=LECTURE_SEULE)
def outil_check(source: Source) -> ResultatCheck:
    """Vérifie un programme Plume sans l'exécuter : syntaxe, variables
    déclarées, portées, nombre d'arguments. Renvoie toutes les erreurs, chacune
    avec sa ligne et sa colonne. À appeler avant run."""
    try:
        compiler(source)
    except ErreurPlume as erreur:
        return {"ok": False, "erreurs": erreurs_json(erreur, source)}
    return {"ok": True, "erreurs": []}


@mcp.tool(name="transpile", annotations=LECTURE_SEULE)
def outil_transpile(
    source: Source,
    backend: Annotated[
        str,
        Field(description=f"Backend à utiliser : {', '.join(sorted(BACKENDS))}"),
    ] = "python",
) -> ResultatTranspile:
    """Traduit un programme Plume, par défaut en Python. Renvoie le code produit
    et, pour Python, la correspondance des lignes avec le programme Plume."""
    if backend not in BACKENDS:
        disponibles = ", ".join(sorted(BACKENDS))
        raise ToolError(f"backend inconnu : {backend!r} (disponibles : {disponibles})")
    try:
        sortie = transpiler(source, backend)
    except ErreurPlume as erreur:
        return {
            "ok": False,
            "code": "",
            "correspondances": None,
            "erreurs": erreurs_json(erreur, source),
        }
    correspondances = None
    if BACKENDS[backend].executable:
        correspondances = {
            str(ligne): [pos.ligne, pos.colonne]
            for ligne, pos in sortie.correspondances.items()
        }
    return {
        "ok": True,
        "code": sortie.code,
        "correspondances": correspondances,
        "erreurs": [],
    }


@mcp.tool(name="format", annotations=LECTURE_SEULE)
def outil_format(source: Source) -> ResultatFormat:
    """Remet un programme Plume en forme : indentation, espaces, parenthèses
    utiles seulement. Attention : les commentaires ne sont pas conservés."""
    try:
        code = transpiler(source, "formateur").code
    except ErreurPlume as erreur:
        return {
            "ok": False,
            "code": "",
            "modifie": False,
            "avertissement": None,
            "erreurs": erreurs_json(erreur, source),
        }
    avertissement = None
    if contient_un_commentaire(source):
        avertissement = "les commentaires (#) ont été supprimés"
    return {
        "ok": True,
        "code": code,
        "modifie": code != source,
        "avertissement": avertissement,
        "erreurs": [],
    }


@mcp.tool(
    name="run",
    annotations=ToolAnnotations(
        read_only_hint=False, destructive_hint=False, open_world_hint=False
    ),
)
def outil_run(
    source: Source,
    delai: Annotated[
        float, Field(ge=0.1, le=10.0, description="Durée maximale, en secondes")
    ] = 2.0,
) -> ResultatRun:
    """Exécute un programme Plume et renvoie ce qu'il affiche. Le programme est
    d'abord vérifié ; il tourne ensuite dans un processus séparé, limité en
    durée et en taille de sortie."""
    # 1. Compiler dans le serveur : rapide, et aucun processus si c'est faux.
    try:
        compiler(source)
    except ErreurPlume as erreur:
        return {
            "statut": "erreur_compilation",
            "sortie": "",
            "erreurs": erreurs_json(erreur, source),
            "duree": 0.0,
        }
    # 2. Exécuter dans le bac à sable.
    r = bac_a_sable.executer(source, delai)
    if r.delai_depasse:
        statut: Statut = "delai_depasse"
    elif r.tronquee:
        statut = "sortie_tronquee"
    elif r.code_retour == 0:
        statut = "ok"
    else:
        statut = "erreur_execution"
    erreurs: list[ErreurJSON] = []
    if statut == "erreur_execution":
        erreurs = [erreur_depuis_stderr(r.stderr)]
    return {"statut": statut, "sortie": r.stdout, "erreurs": erreurs, "duree": r.duree}


def erreur_depuis_stderr(stderr: str) -> ErreurJSON:
    """Reconstruit l'erreur à partir du message de la CLI :
    ``programme.plume:2:5 : erreur d'exécution : division par zéro``."""
    trouve = re.match(r"[^\n]*?:(\d+):(\d+) : ([^:\n]+) : ([^\n]*)", stderr)
    if trouve is None:
        return {
            "genre": "erreur d'exécution",
            "message": stderr.strip(),
            "ligne": None,
            "colonne": None,
            "contexte": stderr.strip(),
        }
    return {
        "genre": trouve[3],
        "message": trouve[4],
        "ligne": int(trouve[1]),
        "colonne": int(trouve[2]),
        "contexte": stderr.strip(),
    }


# --- Les ressources -------------------------------------------------------------


def exemples_disponibles() -> dict[str, Path]:
    """La liste FERMÉE des exemples : nom -> fichier."""
    return {f.stem: f for f in sorted(EXEMPLES.glob("*.plume"))}


def _exemple(nom: str) -> Path:
    # Le nom vient de l'IA : on ne construit jamais de chemin avec, on le
    # cherche dans la liste. « ../specification » n'y est pas : refusé.
    fichier = exemples_disponibles().get(nom)
    if fichier is None:
        raise ResourceNotFoundError(f"exemple inconnu : {nom!r}")
    return fichier


@mcp.resource(
    "plume://specification",
    name="specification",
    description="La spécification complète de Plume : syntaxe, grammaire, règles.",
    mime_type="text/markdown",
)
def specification() -> str:
    return SPECIFICATION.read_text(encoding="utf-8")


@mcp.resource(
    "plume://exemples",
    name="exemples",
    description="La liste des programmes d'exemple, avec leur URI.",
    mime_type="text/markdown",
)
def index_exemples() -> str:
    lignes = ["# Exemples de programmes Plume", ""]
    for nom, fichier in exemples_disponibles().items():
        premiere = fichier.read_text(encoding="utf-8").splitlines()[0]
        description = premiere.lstrip("# ").strip()
        lignes.append(f"- plume://exemples/{nom} : {description}")
    return "\n".join(lignes) + "\n"


@mcp.resource(
    "plume://exemples/{nom}",
    name="exemple",
    description="Le code source d'un programme d'exemple.",
    mime_type="text/plain",
)
def exemple(nom: str) -> str:
    return _exemple(nom).read_text(encoding="utf-8")


@mcp.resource(
    "plume://exemples/{nom}/attendu",
    name="exemple_attendu",
    description="Ce qu'affiche un programme d'exemple.",
    mime_type="text/plain",
)
def exemple_attendu(nom: str) -> str:
    return _exemple(nom).with_suffix(".attendu").read_text(encoding="utf-8")


# --- Les prompts ----------------------------------------------------------------


@mcp.prompt(
    name="ecrire_programme",
    description="Écrire, vérifier et exécuter un programme Plume pour une tâche.",
)
def ecrire_programme(
    tache: Annotated[str, Field(description="Ce que le programme doit faire")],
) -> str:
    return f"""\
Écris un programme dans le langage Plume qui réalise la tâche suivante :

{tache}

Tu ne connais pas Plume. Procède ainsi :
1. Lis la resource plume://specification, puis au moins un exemple
   (la liste est dans plume://exemples).
2. Écris le programme.
3. Appelle l'outil check. S'il signale des erreurs, corrige-les (chacune donne
   sa ligne et sa colonne) et recommence.
4. Appelle l'outil run et vérifie que la sortie correspond à la tâche.
5. Termine par format, et donne le programme final avec sa sortie.
"""


@mcp.prompt(
    name="corriger_programme",
    description="Corriger un programme Plume d'après les erreurs signalées.",
)
def corriger_programme(
    source: Annotated[str, Field(description="Le programme à corriger")],
    erreurs: Annotated[str, Field(description="Les erreurs signalées par check")],
) -> str:
    return f"""\
Ce programme Plume contient des erreurs.

Programme :
{source}

Erreurs signalées :
{erreurs}

Corrige chaque erreur (la ligne et la colonne sont indiquées). Relis la
resource plume://specification si une règle n'est pas claire. Vérifie ensuite
le programme corrigé avec l'outil check, puis exécute-le avec run.
"""

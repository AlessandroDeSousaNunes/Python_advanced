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

from pathlib import Path
from typing import Annotated

from mcp.server.mcpserver import MCPServer
from mcp.server.mcpserver.exceptions import ResourceNotFoundError, ToolError
from mcp_types import ToolAnnotations
from plume.erreurs import ErreurPlume
from plume.etape5_execution.compilateur import (
    BACKENDS,
    analyser_syntaxe,
    compiler,
    decouper,
    transpiler,
)
from pydantic import Field

from serveur_plume import bac_a_sable
from serveur_plume.conversion import (
    contient_un_commentaire,
    erreur_depuis_stderr,
    erreurs_json,
    noeud_json,
    token_json,
)
from serveur_plume.schemas import (
    ErreurJSON,
    ResultatCheck,
    ResultatFormat,
    ResultatParse,
    ResultatRun,
    ResultatTokenize,
    ResultatTranspile,
    Statut,
)

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
    # La source map (extension 13), sous sa forme JSON.
    correspondances = None
    if sortie.sourcemap is not None:
        correspondances = sortie.sourcemap.vers_json()["lignes"]
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
    durée, en taille de sortie et en mémoire. Statuts possibles : ok,
    erreur_compilation, erreur_execution (avec la ligne Plume), delai_depasse,
    sortie_tronquee, memoire_depassee, erreur_interne."""
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
    try:
        r = bac_a_sable.executer(source, delai)
    except OSError as exc:  # le processus n'a pas pu être lancé
        return {
            "statut": "erreur_interne",
            "sortie": "",
            "erreurs": [
                {
                    "genre": "erreur interne",
                    "message": f"exécution impossible : {exc}",
                    "ligne": None,
                    "colonne": None,
                    "contexte": "",
                }
            ],
            "duree": 0.0,
        }
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
        if "mémoire épuisée" in r.stderr or "MemoryError" in r.stderr:
            statut = "memoire_depassee"
    return {"statut": statut, "sortie": r.stdout, "erreurs": erreurs, "duree": r.duree}


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

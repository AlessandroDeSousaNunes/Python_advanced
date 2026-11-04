"""La ligne de commande : ``python -m plume run|transpile|check|fmt|repl``."""

import argparse
import sys
from collections.abc import Callable, Sequence
from pathlib import Path

from plume.compilateur import BACKENDS, compiler, executer, transpiler
from plume.erreurs import ErreurExecution, ErreurPlume, formater
from plume.repl import repl

OK, ERREUR_COMPILATION, ERREUR_EXECUTION = 0, 1, 3  # 2 : réservé par argparse


def lire(chemin: str) -> str | None:
    """Le contenu du fichier, ou ``None`` (message sur ``stderr``) s'il est
    illisible."""
    try:
        return Path(chemin).read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"plume : fichier introuvable : {chemin}", file=sys.stderr)
    except OSError as erreur:
        print(f"plume : impossible de lire {chemin} : {erreur}", file=sys.stderr)
    return None


def signaler(erreur: ErreurPlume, source: str, fichier: str) -> int:
    print(formater(erreur, source, fichier), file=sys.stderr)
    if isinstance(erreur, ErreurExecution):
        return ERREUR_EXECUTION
    return ERREUR_COMPILATION


def avec_source(
    action: Callable[[argparse.Namespace, str], int],
) -> Callable[[argparse.Namespace], int]:
    """Lit le fichier, lance ``action`` et traduit les erreurs Plume."""

    def commande(args: argparse.Namespace) -> int:
        source = lire(args.fichier)
        if source is None:
            return ERREUR_COMPILATION
        try:
            return action(args, source)
        except ErreurPlume as erreur:
            return signaler(erreur, source, args.fichier)

    return commande


@avec_source
def commande_run(args: argparse.Namespace, source: str) -> int:
    executer(source, args.backend)
    return OK


@avec_source
def commande_transpile(args: argparse.Namespace, source: str) -> int:
    code = transpiler(source, args.backend).code
    if args.sortie:
        Path(args.sortie).write_text(code, encoding="utf-8")
    else:
        print(code, end="")
    return OK


@avec_source
def commande_check(args: argparse.Namespace, source: str) -> int:
    compiler(source)
    print(f"{args.fichier} : aucune erreur")
    return OK


@avec_source
def commande_fmt(args: argparse.Namespace, source: str) -> int:
    code = transpiler(source, "formateur").code
    if args.en_place:
        Path(args.fichier).write_text(code, encoding="utf-8")
    else:
        print(code, end="")
    return OK


def commande_repl(args: argparse.Namespace) -> int:
    session = repl()
    reponse = next(session)
    while True:
        try:
            ligne = input(reponse.invite)
        except (EOFError, KeyboardInterrupt):
            print()
            return OK
        reponse = session.send(ligne)
        print(reponse.sortie, end="")


def construire_parseur() -> argparse.ArgumentParser:
    parseur = argparse.ArgumentParser(
        prog="plume", description="Le compilateur du langage Plume."
    )
    sous = parseur.add_subparsers(dest="commande", required=True)
    backends = sorted(BACKENDS)

    run = sous.add_parser("run", help="exécute un programme")
    run.add_argument("fichier")
    run.add_argument("--backend", choices=backends, default="python")
    run.set_defaults(action=commande_run)

    transpile = sous.add_parser("transpile", help="affiche le Python généré")
    transpile.add_argument("fichier")
    transpile.add_argument("-o", "--sortie", help="écrit le code dans ce fichier")
    transpile.add_argument("--backend", choices=backends, default="python")
    transpile.set_defaults(action=commande_transpile)

    check = sous.add_parser("check", help="vérifie sans exécuter")
    check.add_argument("fichier")
    check.set_defaults(action=commande_check)

    fmt = sous.add_parser("fmt", help="réécrit un programme proprement")
    fmt.add_argument("fichier")
    fmt.add_argument(
        "-i", "--en-place", action="store_true", help="réécrit le fichier lui-même"
    )
    fmt.set_defaults(action=commande_fmt)

    sous.add_parser("repl", help="lance l'interpréteur interactif").set_defaults(
        action=commande_repl
    )
    return parseur


def main(argv: Sequence[str] | None = None) -> int:
    try:
        args = construire_parseur().parse_args(argv)
    except SystemExit as sortie:  # --help, commande inconnue…
        return sortie.code if isinstance(sortie.code, int) else ERREUR_COMPILATION
    action: Callable[[argparse.Namespace], int] = args.action
    return action(args)

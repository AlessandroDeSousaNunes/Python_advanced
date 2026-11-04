"""Le REPL : une boucle « lire, exécuter, afficher », écrite comme un
générateur. On lui envoie une saisie avec ``send``, il rend une ``Reponse``.

    session = repl()
    next(session)                   # Reponse(sortie='', invite='plume> ')
    session.send("soit x = 2;")     # Reponse(sortie='', invite='plume> ')
    session.send("x * 21")          # Reponse(sortie='42\\n', invite='plume> ')
"""

import io
from collections.abc import Generator
from contextlib import redirect_stdout
from dataclasses import dataclass

from plume.compilateur import Session, est_expression, est_incomplet
from plume.erreurs import ErreurPlume, formater

INVITE = "plume> "
SUITE = "....> "


@dataclass(frozen=True, slots=True)
class Reponse:
    sortie: str
    invite: str


def repl() -> Generator[Reponse, str, None]:
    session = Session()
    tampon = ""
    sortie = ""
    while True:
        ligne = yield Reponse(sortie, SUITE if tampon else INVITE)
        sortie = ""
        tampon += ligne + "\n"
        if est_incomplet(tampon):
            continue  # un bloc est ouvert : on attend la suite
        source, tampon = tampon, ""
        if source.strip():
            sortie = executer_saisie(session, source)


def executer_saisie(session: Session, source: str) -> str:
    """Exécute une saisie et renvoie ce qu'elle affiche (erreurs comprises).
    Une expression seule est affichée, comme ``affiche``."""
    if est_expression(source):
        source = f"affiche {source.strip()};"
    capture = io.StringIO()
    try:
        with redirect_stdout(capture):
            session.executer(source)
    except ErreurPlume as erreur:
        capture.write(formater(erreur, source, "<repl>") + "\n")
    return capture.getvalue()

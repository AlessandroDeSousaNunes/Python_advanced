"""Exécuter un programme Plume dans un sous-processus, sans risque pour le serveur.

La question de sécurité : c'est une IA qui envoie les programmes, on ne sait
donc pas ce qu'ils font. Plume ne peut ni lire de fichier, ni écouter le
clavier, ni ouvrir le réseau : un programme Plume ne peut que calculer et
afficher. Les deux vrais risques sont donc :

- une boucle sans fin : on coupe le processus après ``delai`` secondes ;
- un affichage sans fin : on ne garde que ``LIMITE`` octets, puis on coupe.

Par précaution, le fils tourne aussi dans un dossier temporaire (supprimé
ensuite), sans entrée clavier, et avec un environnement réduit : il ne voit
pas les variables d'environnement du serveur (mots de passe, clés…).
"""

import os
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import IO

#: Le dossier qui contient le paquet ``plume``.
PROJET = Path(__file__).resolve().parent.parent

#: Au-delà, la sortie est tronquée et le programme arrêté.
LIMITE = 64 * 1024


@dataclass
class Resultat:
    code_retour: int | None  # None : le processus a été tué
    stdout: str
    stderr: str
    duree: float
    delai_depasse: bool
    tronquee: bool


@contextmanager
def processus(commande: list[str], dossier: Path) -> Iterator[subprocess.Popen[bytes]]:
    """Lance le fils, et garantit qu'il est tué et ses tubes fermés à la
    sortie du ``with``, même en cas d'exception."""
    env = {
        "PYTHONPATH": str(PROJET),
        "PYTHONIOENCODING": "utf-8",
        # Windows en a besoin pour démarrer Python ; ce n'est pas un secret.
        "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""),
    }
    fils = subprocess.Popen(
        commande,
        cwd=dossier,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    try:
        yield fils
    finally:
        if fils.poll() is None:
            fils.kill()
        fils.wait()
        for tube in (fils.stdout, fils.stderr):
            if tube is not None:
                tube.close()


def _lire_borne(tube: IO[bytes], morceaux: list[bytes], trop: threading.Event) -> None:
    """Lit le tube jusqu'à LIMITE octets ; au-delà, prévient et s'arrête."""
    total = 0
    while bloc := tube.read(4096):
        if total + len(bloc) > LIMITE:
            morceaux.append(bloc[: LIMITE - total])
            trop.set()
            return
        morceaux.append(bloc)
        total += len(bloc)


def executer(source: str, delai: float = 2.0) -> Resultat:
    """Écrit ``source`` dans un dossier temporaire, puis lance
    ``python -m plume run programme.plume`` dans un sous-processus borné."""
    with tempfile.TemporaryDirectory(prefix="plume_") as nom_dossier:
        dossier = Path(nom_dossier)
        (dossier / "programme.plume").write_text(source, encoding="utf-8")
        commande = [sys.executable, "-m", "plume", "run", "programme.plume"]
        debut = time.perf_counter()
        sortie: list[bytes] = []
        erreurs: list[bytes] = []
        trop = threading.Event()
        with processus(commande, dossier) as fils:
            assert fils.stdout is not None and fils.stderr is not None
            lecteurs = [
                threading.Thread(target=_lire_borne, args=(fils.stdout, sortie, trop)),
                threading.Thread(target=_lire_borne, args=(fils.stderr, erreurs, trop)),
            ]
            for lecteur in lecteurs:
                lecteur.start()
            # On attend la fin du fils, le délai, ou une sortie trop longue.
            depasse = False
            while fils.poll() is None:
                if trop.is_set():
                    break
                if time.perf_counter() - debut > delai:
                    depasse = True
                    break
                time.sleep(0.01)
            if fils.poll() is None:
                fils.kill()
            fils.wait()
            for lecteur in lecteurs:
                lecteur.join()
            code = None if (depasse or trop.is_set()) else fils.returncode
        return Resultat(
            code_retour=code,
            stdout=b"".join(sortie).decode("utf-8", "replace").replace("\r\n", "\n"),
            stderr=b"".join(erreurs).decode("utf-8", "replace").replace("\r\n", "\n"),
            duree=round(time.perf_counter() - debut, 3),
            delai_depasse=depasse,
            tronquee=trop.is_set(),
        )

"""Exécuter un programme Plume dans un sous-processus, sans risque pour le serveur.

La question de sécurité : c'est une IA qui envoie les programmes, personne ne
les a relus.

Les risques, et la protection de chacun :

- boucle sans fin : le fils est tué après ``delai`` secondes ;
- affichage sans fin : on ne garde que ``LIMITE`` octets par flux, puis on tue ;
- mémoire (un entier qui double sans fin) : ``RLIMIT_AS`` posé par le fils
  lui-même, sous Linux et macOS seulement (le module ``resource`` n'existe pas
  sous Windows) ;
- plantage du serveur : le programme ne tourne jamais dans le serveur
  (aucun ``exec`` ici), seulement dans un processus séparé ;
- fichiers qui traînent : dossier temporaire supprimé par ``with`` ;
- lecture de l'entrée du serveur : ``stdin=DEVNULL`` (en stdio, l'entrée du
  serveur est le canal MCP) ;
- fuite de secrets : environnement réduit, le fils ne voit pas les variables
  du serveur.

Ce que ces protections ne couvrent PAS : l'accès aux fichiers, au réseau, aux
autres programmes. C'est la conception de Plume qui protège le système :

- Plume n'a ni fichiers, ni réseau, ni import, ni lecture au clavier : un
  programme ne peut que calculer et afficher ;
- un texte ``"..."`` est traduit avec ``repr`` : un texte comme
  ``"'); import os; ('"`` reste un simple texte en Python ;
- un nom de variable ne contient que lettres, chiffres et ``_``, et ne commence
  jamais par ``_`` ; les noms gênants (``print``, ``exec``, ``open``,
  ``__import__``…) sont renommés ``_v_...`` : impossible d'appeler une
  fonction de Python ;
- un commentaire ``#`` est jeté par le lexer : il n'arrive jamais dans le
  Python généré.

Aucun programme Plume ne peut donc produire du Python que nous n'avons pas
prévu. Un langage qui offrirait ``lis_fichier(...)`` demanderait un vrai bac à
sable (conteneur, utilisateur dédié, filtre des appels système).
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

#: Mémoire maximale du fils (Linux et macOS seulement).
MEMOIRE = 512 * 1024 * 1024

#: Le module ``resource`` (limite de mémoire) n'existe pas sous Windows.
LIMITE_MEMOIRE_POSSIBLE = sys.platform != "win32"


def commande_fils(fichier: str) -> list[str]:
    """La commande qui lance la CLI de Plume sur ``fichier``.

    Sous Linux et macOS, le fils pose lui-même sa limite de mémoire, AVANT
    d'importer Plume (``preexec_fn`` est déconseillé : le SDK utilise des
    threads)."""
    if not LIMITE_MEMOIRE_POSSIBLE:
        return [sys.executable, "-m", "plume", "run", fichier]
    code = (
        "import resource, sys; "
        f"resource.setrlimit(resource.RLIMIT_AS, ({MEMOIRE}, {MEMOIRE})); "
        "from plume.etape5_execution.cli import main; "
        "sys.exit(main(sys.argv[1:]))"
    )
    return [sys.executable, "-c", code, "run", fichier]


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
        "PYTHONPATH": str(PROJET),  # pour que le fils trouve le paquet plume
        "PATH": os.environ.get("PATH", ""),
        "PYTHONUTF8": "1",  # les accents passent quel que soit le système
        "PYTHONIOENCODING": "utf-8",
    }
    if sys.platform == "win32":
        # Windows en a besoin pour démarrer Python ; ce n'est pas un secret.
        env["SYSTEMROOT"] = os.environ.get("SYSTEMROOT", "")
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
        commande = commande_fils("programme.plume")
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

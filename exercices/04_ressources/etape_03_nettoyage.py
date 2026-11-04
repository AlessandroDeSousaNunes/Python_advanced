"""Étape 3 : ``finally`` et nettoyage.

Libérer une ressource dans tous les cas, sans ``with`` : c'est exactement ce
que ``with`` fera pour nous aux étapes suivantes.
"""

from collections.abc import Callable, Iterable


class Ressource:
    """Une ressource factice (connexion, verrou…) qui note ce qu'on lui fait
    dans un journal partagé. Fournie."""

    def __init__(
        self,
        nom: str,
        journal: list[str],
        *,
        echec_ouverture: bool = False,
        echec_fermeture: bool = False,
    ) -> None:
        self.nom = nom
        self.journal = journal
        self.ouverte = False
        self.echec_ouverture = echec_ouverture
        self.echec_fermeture = echec_fermeture

    def ouvrir(self) -> None:
        if self.echec_ouverture:
            self.journal.append(f"échec ouverture {self.nom}")
            raise OSError(f"ouverture de {self.nom} impossible")
        self.ouverte = True
        self.journal.append(f"ouvre {self.nom}")

    def fermer(self) -> None:
        self.ouverte = False
        self.journal.append(f"ferme {self.nom}")
        if self.echec_fermeture:
            raise OSError(f"fermeture de {self.nom} impossible")

    def __repr__(self) -> str:
        return f"Ressource({self.nom!r})"


class ErreurFermeture(Exception):
    """Une ou plusieurs fermetures ont échoué."""

    def __init__(self, erreurs: list[Exception]) -> None:
        self.erreurs = erreurs
        super().__init__(f"{len(erreurs)} fermeture(s) en échec")


def utiliser[T](ressource: Ressource, action: Callable[[Ressource], T]) -> T:
    """Ouvre la ressource, renvoie ``action(ressource)``, et ferme la
    ressource dans tous les cas. Si l'ouverture échoue, on ne ferme pas."""
    # ouvrir est avant le try : si elle échoue, le finally ne s'exécute pas.
    ressource.ouvrir()
    try:
        return action(ressource)
    finally:
        ressource.fermer()


def deroulement(
    action: Callable[[], object],
    suite: Callable[[list[str]], object] | None = None,
) -> list[str]:
    """Exécute ``action()`` dans un ``try/except Exception/else/finally``, et
    renvoie la liste des blocs exécutés, dans l'ordre : ``"try"``,
    ``"except"``, ``"else"``, ``"finally"``.

    Si ``suite`` est fournie, elle est appelée dans le ``else`` (donc
    seulement si ``action`` a réussi), avec la liste des blocs. Une exception
    levée par ``suite`` n'est **pas** rattrapée par le ``except``."""
    blocs: list[str] = []
    try:
        blocs.append("try")
        action()
    except Exception:
        blocs.append("except")
    else:
        blocs.append("else")
        if suite is not None:
            suite(blocs)
    finally:
        blocs.append("finally")
    return blocs


def fermer_tout(ressources: Iterable[Ressource]) -> None:
    """Ferme chaque ressource, dans l'ordre donné, même si certaines
    fermetures échouent. Si au moins une a échoué, lève ``ErreurFermeture``
    avec la liste des erreurs, causée par la première."""
    erreurs: list[Exception] = []
    for ressource in ressources:
        try:
            ressource.fermer()
        except Exception as e:
            erreurs.append(e)
    if erreurs:
        raise ErreurFermeture(erreurs) from erreurs[0]


def avec_ressources[T](
    ressources: list[Ressource], action: Callable[[list[Ressource]], T]
) -> T:
    """Ouvre les ressources dans l'ordre, renvoie ``action(ressources)``, puis
    ferme **celles qui ont été ouvertes**, dans l'ordre inverse, avec
    ``fermer_tout``. Si une ouverture échoue, les ressources déjà ouvertes
    sont fermées et l'erreur d'ouverture se propage."""
    ouvertes: list[Ressource] = []
    try:
        for ressource in ressources:
            ressource.ouvrir()
            ouvertes.append(ressource)
        return action(ressources)
    finally:
        fermer_tout(reversed(ouvertes))

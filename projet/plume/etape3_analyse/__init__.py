"""Étape 3 : VÉRIFIER le sens du programme.

Entre : l'arbre de l'étape 2.
Sort : le feu vert (un objet ``Analyse``), ou la liste de toutes les erreurs.

- ``semantique.py`` (principal) : parcourt l'arbre et vérifie qu'une variable
  est déclarée avant usage, qu'un nom n'est pas déclaré deux fois, que le
  nombre d'arguments est le bon… On vérifie des NOMS, aucun calcul n'est fait.
- ``symboles.py`` : la table des noms déclarés, rangée bloc par bloc (une
  pile de portées).
"""

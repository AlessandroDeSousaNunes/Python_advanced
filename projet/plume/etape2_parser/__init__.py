"""Étape 2 : ASSEMBLER les tokens en arbre.

Entre : les tokens de l'étape 1.
Sort : un arbre, par exemple ``Declaration(nom="x", valeur=Entier(2))``.

- ``parser.py`` (principal) : regarde le premier token pour choisir un modèle
  (``soit`` = déclaration, ``si`` = condition…), puis remplit les trous du
  modèle dans l'ordre. Pour les calculs, chaque opérateur a une force : les
  plus forts sont regroupés en premier (méthode de Pratt).
- ``noeuds.py`` : les sortes de nœuds de l'arbre (``Si``, ``Binaire``,
  ``Appel``…), sous forme de dataclasses.
"""

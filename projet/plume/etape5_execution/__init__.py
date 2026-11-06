"""Étape 5 : EXÉCUTER, et tout relier.

Entre : le texte du programme.
Sort : ce qui s'affiche à l'écran.

- ``compilateur.py`` (principal) : la façade. Elle enchaîne les étapes 1 à 4,
  puis donne le Python à Python (``exec``). Si Python plante, elle retrouve la
  ligne Plume fautive.
- ``cli.py`` : les commandes ``python -m plume run | transpile | check | fmt | repl``.
- ``repl.py`` : le mode interactif (``plume>``).
"""

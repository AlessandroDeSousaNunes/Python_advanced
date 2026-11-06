"""Plume : un petit langage aux mots-clés français, transpilé en Python.

Le code est rangé en 5 dossiers, un par étape, dans l'ordre du voyage d'un
programme. Dans chaque dossier, un fichier principal et ses petits fichiers.

    texte ─▶ 1 lexer ─▶ 2 parser ─▶ 3 analyse ─▶ 4 traduction ─▶ 5 exécution
             découper    assembler   vérifier     traduire        exécuter

etape1_lexer/       lexer.py       ← principal : découpe le texte en tokens
                    tokens.py        les étiquettes des tokens
                    flux.py          regarder le token suivant sans le prendre

etape2_parser/      parser.py      ← principal : assemble les tokens en arbre
                    noeuds.py        les sortes de nœuds de l'arbre

etape3_analyse/     semantique.py  ← principal : vérifie le sens du programme
                    symboles.py      la table des noms déclarés

etape4_traduction/  generateur.py  ← principal : traduit l'arbre en Python
                    emetteur.py      écrit des lignes bien indentées
                    backend.py       le contrat commun des traducteurs
                    formateur.py     un 2e traducteur : réécrit du Plume propre

etape5_execution/   compilateur.py ← principal : enchaîne tout, puis exécute
                    cli.py           les commandes (python -m plume run …)
                    repl.py          le mode interactif

erreurs.py          les erreurs, communes à toutes les étapes
__main__.py         permet « python -m plume »
"""

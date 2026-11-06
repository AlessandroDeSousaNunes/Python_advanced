"""Étape 1 : DÉCOUPER le texte en tokens.

Entre : le texte du programme, par exemple ``soit x = 2;``.
Sort : des tokens (un mot + son étiquette + sa position) :
``[SOIT soit] [IDENT x] [EGAL =] [ENTIER 2] [POINT_VIRGULE ;] [FIN]``.

- ``lexer.py`` (principal) : lit le texte lettre par lettre. Un mot continue
  tant que la lettre suivante peut en faire partie ; une espace ou un symbole
  l'arrête. Les espaces et les commentaires sont jetés.
- ``tokens.py`` : la liste des étiquettes possibles (mots-clés, symboles…) et
  la classe ``Token``.
- ``flux.py`` : permet au parser de regarder le token suivant sans le prendre.
"""

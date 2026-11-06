# Python avancé : mes rendus

Alessandro De Sousa Nunes

Ce dépôt contient uniquement mes réponses aux exercices et mes travaux à rendre.
Les énoncés et les tests sont dans le dépôt du cours.

## Exercices

| Chapitre | Étapes | Tests |
|---|---|---|
| `exercices/00_bases` | 1 à 6 | ✅ |
| `exercices/01_modele_objet` | 1 à 6 | ✅ |
| `exercices/02_fonctions` | 1 à 6 | ✅ |
| `exercices/03_iterateurs` | 1 à 6 | ✅ |
| `exercices/04_ressources` | 1 à 6 | ✅ |
| `exercices/05_typage` | 1 à 6 | ✅ (mypy --strict compris) |

`python -m pytest exercices` dans le dépôt du cours : 1091 tests passent.

## Projet langage : Plume

Un petit langage aux mots-clés français, transpilé en Python (`projet/`).

- `projet/specification.md` : la spécification (à faire valider) ;
- `projet/exemples/` : cinq programmes et leurs sorties attendues ;
- `projet/plume/` : le compilateur (lexer, parser de Pratt, analyse sémantique,
  génération de Python, CLI, REPL, formateur) ;
- `projet/serveur_plume/` : le serveur MCP (outils, ressources, prompts) ;
- `projet/tests/` : les tests de chaque étape (229 tests, `mypy --strict` compris) ;
- `projet/MEMO_TECHNIQUE.md` : comment fonctionne le code, fichier par fichier.

```bash
cd projet
python -m plume run exemples/04_fonctions.plume
python -m plume repl
```

Langage : étapes 1 à 10 faites. Serveur MCP : fait (`python -m serveur_plume`). Extensions 11 à 13 : pas encore.

# Mémo technique : Plume

Ce mémo explique comment fonctionne le code de Plume : le chemin d'un programme, puis chaque fichier, avec ce qu'il fait et comment il le fait.

## 1. En gros

Plume est un **transpileur** : il traduit un programme Plume en code Python, puis demande à Python de l'exécuter. Plume ne calcule rien lui-même.

```
texte ──lexer──▶ tokens ──parser──▶ arbre ──analyse──▶ arbre vérifié ──générateur──▶ Python ──exec──▶ résultat
```

| Étape | Fichier | Entre | Sort |
|---|---|---|---|
| Découper | `lexer.py` | le texte (`str`) | des `Token`, un par un |
| Assembler | `parser.py` | les `Token` | un arbre (`Programme`) |
| Vérifier | `semantique.py` | l'arbre | une `Analyse` (ou des erreurs) |
| Traduire | `generateur.py` | l'arbre + l'`Analyse` | du texte Python (`Sortie`) |
| Exécuter | `compilateur.py` | le texte Python | ce qui s'affiche |

Exemple : `soit x = 2;`

1. **lexer** : `[SOIT soit] [IDENT x] [EGAL =] [ENTIER 2] [POINT_VIRGULE ;] [FIN]`
2. **parser** : `Declaration(nom="x", valeur=Entier(2))`
3. **analyse** : `x` n'existe pas encore, on peut le déclarer ✓
4. **générateur** : `x = 2`
5. **Python** exécute `x = 2`

## 2. Les fichiers, un par un

Le paquet `plume/` est rangé en 5 dossiers, un par étape, dans l'ordre :

```
plume/
├── etape1_lexer/       lexer.py (principal), tokens.py, flux.py
├── etape2_parser/      parser.py (principal), noeuds.py
├── etape3_analyse/     semantique.py (principal), symboles.py
├── etape4_traduction/  generateur.py (principal), emetteur.py, backend.py, formateur.py
├── etape5_execution/   compilateur.py (principal), cli.py, repl.py
├── erreurs.py          les erreurs, communes à toutes les étapes
└── __main__.py         « python -m plume »
```

Chaque dossier a un `__init__.py` qui résume son étape : ce qui entre, ce qui sort, le rôle de chaque fichier.

### `erreurs.py` : les positions et les erreurs

- **Ce qu'il fait** : définit `Position` (ligne, colonne) et la famille d'erreurs, puis les met en forme pour l'utilisateur.
- **Comment** :
  - `ErreurPlume` est la racine. En dessous, une erreur par étape : `ErreurLexicale`, `ErreurSyntaxe`, `ErreurSemantique` et `ErreurExecution`.
  - `ErreursMultiples` regroupe plusieurs erreurs, pour les signaler toutes d'un coup.
  - `formater(erreur, source, fichier)` produit `fichier:ligne:colonne : genre : message`, puis la ligne fautive et un `^` sous la colonne.

### `etape1_lexer/tokens.py` : les sortes de mots

- **Ce qu'il fait** : décrit ce qu'est un token, c'est-à-dire un mot du programme avec son étiquette.
- **Comment** :
  - `TokenKind` est une `Enum` : la liste fermée de toutes les étiquettes (`SOIT`, `IDENT`, `ENTIER`, `PLUS`…).
  - `Token` est une dataclass gelée qui réunit l'étiquette (`kind`), le texte exact (`lexeme`) et la `position`.
  - `MOTS_CLES` (mot → étiquette) et `SYMBOLES` sont **construits à partir de l'Enum**. `SYMBOLES` est trié du plus long au plus court.

### `etape1_lexer/lexer.py` : découper le texte

- **Ce qu'il fait** : transforme le texte en tokens.
- **Comment** : un curseur `i` avance caractère par caractère, et chaque tour de boucle regarde le caractère courant.

| Le caractère est… | Le lexer… |
|---|---|
| une espace, une tabulation | la saute (pas de token) |
| un saut de ligne | passe à la ligne suivante (pas de token) |
| `#` | saute jusqu'à la fin de la ligne (commentaire) |
| un chiffre | lit tous les chiffres qui suivent → `ENTIER` |
| une lettre | lit lettres, chiffres et `_` → mot-clé si le mot est dans `MOTS_CLES`, sinon `IDENT` |
| `"` | lit jusqu'au `"` suivant, en décodant `\n` `\t` `\"` `\\` → `TEXTE` |
| autre chose | essaie les `SYMBOLES`, le plus long d'abord (`<=` avant `<`) |
| rien de tout ça | `ErreurLexicale` : caractère inattendu |

`tokenize` est un **générateur** (`yield`) : il ne découpe que ce qu'on lui demande. Il termine toujours par un token `FIN`.

### `etape1_lexer/flux.py` : regarder devant

- **Ce qu'il fait** : permet au parser de regarder le token suivant **sans le consommer**.
- **Comment** : `Flux[T]` garde les éléments déjà lus dans un tampon (`deque`). `regarde(n)` lit dans la source seulement ce qui manque, et `avance()` consomme l'élément courant.

### `etape2_parser/noeuds.py` : l'arbre

- **Ce qu'il fait** : définit une classe par sorte de nœud.
  - Expressions (`Expr`) : `Entier`, `Texte`, `Booleen`, `Variable`, `Unaire`, `Binaire`, `Appel`.
  - Instructions (`Instr`) : `Declaration`, `Affectation`, `Affiche`, `Si`, `TantQue`, `Fonction`, `Retourne`, `ExprInstr`.
  - La racine : `Programme`.
- **Comment** :
  - Ce sont des dataclasses gelées.
  - Chaque nœud a un champ `pos` exclu de `==` et du `repr` : deux arbres de même forme sont égaux.
  - `afficher_arbre` dessine n'importe quel arbre grâce à `dataclasses.fields`.

### `etape2_parser/parser.py` : assembler l'arbre

- **Ce qu'il fait** : transforme les tokens en arbre et signale les erreurs de syntaxe.
- **Comment** :
  - **Instructions** : `instruction()` regarde le **premier token** pour choisir un modèle (`soit` → `declaration()`, `si` → `si()`…). Chaque méthode remplit son modèle dans l'ordre avec `attend(…)`, qui consomme le token attendu ou lève « `';'` attendu ».
  - **Calculs, avec la méthode de Pratt** : chaque opérateur a une **force** (`+` = 5, `*` = 6). `expression(precedence)` lit le début, puis tant que l'opérateur suivant est **plus fort** que `precedence`, il prend ce qui a été lu comme opérande gauche. Résultat : `1 + 2 * 3` donne `1 + (2 * 3)`.
  - Les règles sont rangées dans deux tables, `PREFIXES` et `INFIXES`, remplies par les **décorateurs paramétrés** `@prefixe(...)` et `@infixe(..., precedence=...)`.
  - **Erreurs** : `_proteger` attrape une `ErreurSyntaxe`, la note, puis `_synchroniser` saute jusqu'au prochain `;` ou mot-clé. À la fin, `parse()` lève une seule `ErreursMultiples`.

### `etape3_analyse/symboles.py` : la table des noms

- **Ce qu'il fait** : retient les noms déclarés (pas leurs valeurs), bloc par bloc.
- **Comment** :
  - C'est une **pile de portées**, chaque portée étant un dictionnaire nom → `Symbole`.
  - `with table.portee():` empile une portée à l'entrée d'un bloc et la retire à la sortie (`@contextmanager`).
  - `chercher(nom)` cherche du bloc le plus intérieur vers le niveau principal.

### `etape3_analyse/semantique.py` : vérifier le sens

- **Ce qu'il fait** : refuse les programmes bien écrits mais qui n'ont pas de sens.
- **Comment** :
  - `Analyseur` parcourt l'arbre. `singledispatchmethod` appelle la bonne variante selon le **type** du nœud.
  - Il vérifie :
    - toute variable est déclarée avant usage ;
    - aucun nom encore visible n'est redéclaré ;
    - `retourne` n'apparaît que dans une fonction ;
    - les fonctions sont déclarées au niveau principal ;
    - le nombre d'arguments est le bon.
  - Il note aussi, pour chaque fonction, les variables globales qu'elle modifie (`Analyse.globales_modifiees`).
- **Pourquoi interdire la redéclaration** : Python n'a pas de portée de bloc. Sans cette règle, deux variables Plume de même nom deviendraient une seule variable en Python.

### `etape4_traduction/emetteur.py` : écrire du code indenté

- **Ce qu'il fait** : accumule les lignes du code produit.
- **Comment** :
  - `ligne(texte)` ajoute une ligne au niveau d'indentation courant.
  - `with bloc():` monte d'un niveau, et ajoute `pass` si le bloc est resté vide.
  - `with depuis(position):` note de quelle ligne Plume vient chaque ligne produite. C'est le dictionnaire `correspondances`.

### `etape4_traduction/generateur.py` : traduire en Python

- **Ce qu'il fait** : écrit le Python équivalent de l'arbre.
- **Comment** :
  - `match` / `case` sur chaque sorte de nœud (`Si` → `if`, `TantQue` → `while`…), et `assert_never` vérifie avec mypy qu'aucune sorte n'est oubliée.
  - Quatre précautions :
    1. chaque calcul est mis entre parenthèses ;
    2. les noms qui gênent Python (`print`, `len`…) sont renommés `_v_…` ;
    3. `affiche` devient un simple `print` ; une valeur qui peut être `vrai`, `faux` ou `rien` passe par `_texte()` (le **prélude**) pour s'afficher en français ;
    4. `global x` est ajouté quand une fonction modifie une globale.

### `etape4_traduction/backend.py` : le contrat d'un traducteur

- **Ce qu'il fait** : définit ce que doit avoir un traducteur.
- **Comment** :
  - `Backend` est un `Protocol` : un `nom`, une `extension`, un booléen `executable` et une méthode `generer(programme, analyse) -> Sortie`.
  - `Sortie` contient le code produit et les correspondances de lignes.

### `etape4_traduction/formateur.py` : réécrire du Plume proprement

- **Ce qu'il fait** : un deuxième backend, qui réécrit le programme en Plume bien présenté au lieu de le traduire en Python.
- **Comment** : même forme que le générateur. Il ne met que les parenthèses nécessaires, en comparant les forces des opérateurs.

### `etape5_execution/compilateur.py` : la façade

- **Ce qu'il fait** : le seul point d'entrée vers la chaîne. La ligne de commande, le REPL et le serveur MCP passent tous par lui.
- **Comment** :
  - `compiler(source)` enchaîne parse et analyse.
  - `transpiler(source, backend)` produit le code.
  - `executer(source)` compile, puis `compile()` + `exec()` le Python.
  - Si Python plante, `traduire()` remonte le traceback jusqu'à une ligne du code généré (fichier `"<plume>"`), retrouve la ligne Plume grâce aux correspondances, et lève une `ErreurExecution` en français, avec `raise … from`.
  - `Session` garde l'état entre deux saisies du REPL.

### `etape5_execution/cli.py` et `__main__.py` : la ligne de commande

- **Ce qu'il fait** : `python -m plume run|transpile|check|fmt|repl fichier`.
- **Comment** :
  - `argparse` lit la commande, puis la commande appelle la façade.
  - Les erreurs sont affichées sur `stderr` avec `formater`.
  - Code de sortie : 0 si tout va bien, 1 pour une erreur de compilation, 3 pour une erreur d'exécution.

### `etape5_execution/repl.py` : le mode interactif

- **Ce qu'il fait** : `plume>` attend une ligne, l'exécute et affiche le résultat.
- **Comment** :
  - C'est un **générateur** : `ligne = yield Reponse(...)`, et on lui envoie chaque saisie avec `send`.
  - Tant qu'un `{` n'est pas fermé, il attend la suite.
  - Une expression seule (`x * 21`) est affichée.

### `tests/` : les tests

Un fichier par étape (`test_etape_02_tokens.py`…). Chaque test vérifie un comportement précis, par exemple que `1 + 2 * 3` donne bien `1 + (2 * 3)`. Le test central exécute chaque programme de `exemples/` et compare sa sortie au fichier `.attendu`.

```bash
python -m pytest projet
```

### `serveur_plume/` : le serveur MCP

- **Ce qu'il fait** : permet à une IA (Claude, par exemple) d'apprendre Plume et de l'utiliser, sans lire le code du projet.
- **Comment** :
  - `serveur.py` crée `MCPServer("plume")`, puis expose trois sortes de choses avec des décorateurs :
    - **6 outils** (`@mcp.tool`), que l'IA appelle :
      - `tokenize` découpe en tokens ;
      - `parse` construit l'arbre ;
      - `check` vérifie ;
      - `transpile` traduit ;
      - `format` remet en forme ;
      - `run` exécute.

      Chaque outil appelle la façade `plume.etape5_execution.compilateur` et renvoie du JSON (`TypedDict`).
    - **4 ressources** (`@mcp.resource`), que l'IA lit : la spécification, la liste des exemples, chaque exemple et sa sortie attendue.
    - **2 prompts** (`@mcp.prompt`), des modes d'emploi : `ecrire_programme(tache)` et `corriger_programme(source, erreurs)`.
  - `bac_a_sable.py` exécute un programme dans un **sous-processus** :
    - un dossier temporaire ;
    - une durée maximale, puis le processus est tué ;
    - une sortie limitée à 64 Kio ;
    - pas d'accès aux variables d'environnement du serveur.
  - `__main__.py` : `python -m serveur_plume` lance le serveur en stdio. L'IA lui parle par l'entrée et la sortie standard.

## 3. Ce qui garde quoi

| Moment | Ce qu'on manipule | Où c'est rangé |
|---|---|---|
| Traduction | des **noms** (« x est une variable ») | `TableSymboles` |
| Exécution | des **valeurs** Python (`int`, `str`, `bool`, `None`) | le dictionnaire de variables de `exec` |

Plume n'est pas réactif : le programme s'exécute une seule fois, de haut en bas.

## 4. Les notions du cours

| Chapitre | Où dans Plume |
|---|---|
| 1. Modèle objet | `Enum` (`TokenKind`), dataclasses gelées (`Token`, nœuds) |
| 2. Fonctions | décorateurs paramétrés `@prefixe` / `@infixe`, `singledispatchmethod` |
| 3. Itérateurs | `tokenize` est un générateur, `Flux[T]`, le REPL piloté par `send` |
| 4. Ressources | hiérarchie d'erreurs, `raise … from`, `@contextmanager` (portées, blocs) |
| 5. Typage | `match` + `assert_never`, `Protocol Backend`, `mypy --strict` |

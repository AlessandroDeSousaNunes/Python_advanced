# Spécification de Plume

## Identité

| | |
|---|---|
| Nom | Plume |
| Extension | `.plume` |
| Idée | Le plus petit langage impératif possible qui couvre toute la chaîne de compilation. Des mots-clés en français, des accolades pour les blocs, un `;` à la fin de chaque instruction. Trois sortes de valeurs seulement : des entiers, des textes et des booléens. Il s'adresse à un débutant qui veut lire un programme sans connaître de langage. |
| Cible | Python 3.12, sous forme de texte. |

## Un programme pour donner le ton

```
# Affiche les factorielles de 0 à 5.
fonction factorielle(n) {
    si n <= 1 {
        retourne 1;
    }
    retourne n * factorielle(n - 1);
}

soit k = 0;
tantque k <= 5 {
    affiche k, factorielle(k);
    k = k + 1;
}

si factorielle(5) > 100 et non faux {
    affiche "c'est grand !";
} sinon {
    affiche "c'est petit";
}
```

## Lexique

- **Blancs et sauts de ligne** : ignorés. La mise en forme est libre ; les instructions se terminent par `;`.
- **Commentaires** : de `#` jusqu'à la fin de la ligne.
- **Nombres** : uniquement des entiers positifs écrits en chiffres ASCII (`0`, `42`, `007`). Il n'y a pas de décimaux. Un nombre collé à une lettre (`12abc`) est une erreur. Un nombre négatif s'écrit avec le `-` unaire : `-5`.
- **Textes** : entre guillemets droits, `"..."`, sur une seule ligne. Échappements : `\n` (saut de ligne), `\t` (tabulation), `\"` et `\\`. Tout autre échappement est une erreur.
- **Identifiants** : une lettre (accents permis), puis des lettres, des chiffres ou `_`. Un identifiant ne peut pas commencer par `_` : ce préfixe est réservé au code Python généré.
- **Mots-clés** : `soit si sinon tantque fonction retourne affiche vrai faux et ou non`.
- **Symboles** : `+ - * / % == != < <= > >= = ( ) { } , ;`.

Un mot-clé n'est reconnu que s'il forme un mot entier : `sinon_si` et `siffler` sont des identifiants.

## Grammaire (EBNF)

```ebnf
programme   = { instruction } FIN ;
instruction = declaration | affectation | affiche | si | tantque
            | fonction | retour | expression ";" ;

declaration = "soit" IDENT "=" expression ";" ;
affectation = IDENT "=" expression ";" ;
affiche     = "affiche" expression { "," expression } ";" ;
si          = "si" expression bloc [ "sinon" ( si | bloc ) ] ;
tantque     = "tantque" expression bloc ;
fonction    = "fonction" IDENT "(" [ IDENT { "," IDENT } ] ")" bloc ;
retour      = "retourne" [ expression ] ";" ;
bloc        = "{" { instruction } "}" ;

expression  = ou ;
ou          = et { "ou" et } ;
et          = negation { "et" negation } ;
negation    = "non" negation | comparaison ;
comparaison = somme { ( "==" | "!=" | "<" | "<=" | ">" | ">=" ) somme } ;
somme       = produit { ( "+" | "-" ) produit } ;
produit     = unaire { ( "*" | "/" | "%" ) unaire } ;
unaire      = "-" unaire | appel ;
appel       = IDENT "(" [ expression { "," expression } ] ")" | primaire ;
primaire    = ENTIER | TEXTE | "vrai" | "faux" | IDENT | "(" expression ")" ;
```

## Priorité et associativité des opérateurs

Du moins prioritaire au plus prioritaire.

| Niveau | Opérateurs | Associativité |
|---|---|---|
| 1 | `ou` | gauche |
| 2 | `et` | gauche |
| 3 | `non` (unaire) | préfixe |
| 4 | `==` `!=` `<` `<=` `>` `>=` | gauche |
| 5 | `+` `-` | gauche |
| 6 | `*` `/` `%` | gauche |
| 7 | `-` (unaire) | préfixe |
| 8 | appel de fonction `f(...)` | — |

Points particuliers :

- `a < b < c` se lit `(a < b) < c`, et **pas** comme une comparaison chaînée à la Python.
- `non a == b` se lit `non (a == b)` : `non` porte sur toute la comparaison.
- `-a * b` se lit `(-a) * b` : le `-` unaire ne porte que sur ce qui le suit immédiatement.
- Seule une fonction **nommée** peut être appelée : `f(1)` est valide, `f(1)(2)` ne l'est pas.

## Sémantique

- **Valeurs** : des entiers (sans limite de taille), des textes et des booléens `vrai` / `faux`. Une fonction qui se termine sans `retourne` (ou avec `retourne;` seul) renvoie l'absence de valeur, affichée `rien`.
- **Opérateurs** :
  - `+ - *` sur des entiers ; `+` colle aussi deux textes (`"a" + "b"` donne `"ab"`) ;
  - `/` est la **division entière**, arrondie vers le bas (`7 / 2` vaut `3`, `-7 / 2` vaut `-4`), et `%` le reste qui va avec ;
  - `==` et `!=` comparent deux valeurs quelconques (`1 == "1"` est faux) ; `< <= > >=` comparent deux entiers ou deux textes (ordre alphabétique) ;
  - `et`, `ou`, `non` attendent des booléens.
- **Variables** : elles se déclarent avec `soit` avant d'être utilisées, puis se modifient avec `=`. La valeur d'une déclaration ne peut pas utiliser la variable qu'elle déclare : `soit x = x;` est une erreur.
- **Blocs et portées** : chaque bloc `{ }` ouvre une portée. Une variable n'existe que de sa déclaration jusqu'à la fin de son bloc. **On ne peut pas redéclarer un nom tant qu'il est visible** (ni le masquer dans un bloc intérieur, ni dans une fonction). Deux blocs frères peuvent en revanche réutiliser le même nom.
- **Fonctions** : elles se déclarent **au niveau principal seulement** (pas dans un bloc, pas dans une autre fonction), avant d'être appelées. Une fonction peut s'appeler elle-même (récursion). Le nombre d'arguments est vérifié à la compilation. Une fonction peut lire et modifier les variables du niveau principal déclarées **avant** elle. Les paramètres se comportent comme des variables du corps de la fonction.
- **`retourne`** : seulement dans une fonction. Il arrête la fonction et renvoie la valeur (ou rien).
- **`si` / `sinon`** : `sinon si` permet d'enchaîner les tests. **`tantque`** répète son bloc tant que la condition est vraie.
- **Affichage** : `affiche a, b, c;` affiche les valeurs séparées par une espace, puis passe à la ligne. Les booléens s'affichent `vrai` / `faux`, l'absence de valeur `rien`, les textes sans guillemets.
- **Instruction-expression** : une expression seule suivie de `;` est évaluée et sa valeur est oubliée. C'est utile pour appeler une fonction : `saluer("Ada");`.
- **Fonctions prédéfinies** : `texte(valeur)` renvoie la valeur sous forme de texte, telle que `affiche` l'écrirait (`texte(vrai)` donne `"vrai"`). Son nom est réservé : on ne peut pas déclarer une variable ou une fonction `texte`.
- **Erreurs de compilation** : caractère inconnu, texte non terminé, instruction mal formée, `;` oublié, variable ou fonction inconnue, double déclaration, mauvais nombre d'arguments, `retourne` hors d'une fonction, fonction déclarée dans un bloc. Toutes les erreurs d'un programme sont signalées ensemble, chacune avec sa ligne et sa colonne.
- **Erreurs d'exécution** : division par zéro, opération entre types incompatibles (`1 + "a"`), récursion trop profonde. Le programme s'arrête avec un message qui désigne **la ligne du programme Plume** fautive.

## Programmes d'exemple

| Fichier | Ce qu'il montre |
|---|---|
| `01_bonjour.plume` | textes, variables, calculs et priorités, division entière, échappements |
| `02_conditions.plume` | `si` / `sinon si` / `sinon`, comparaisons, booléens, `et` `ou` `non` |
| `03_boucles.plume` | `tantque`, accumulation, FizzBuzz |
| `04_fonctions.plume` | fonctions, récursion, `retourne`, fonction sans résultat, `texte()` |
| `05_portees.plume` | blocs et portées, fonction qui modifie une variable globale, noms Python (`len`, `print`) |

## Limites assumées

- Pas de décimaux, pas de listes, pas de lecture au clavier ni de fichiers : un programme Plume ne peut que calculer et afficher. Il est donc sûr à exécuter.
- Pas de boucle `pour` : `tantque` suffit.
- Les types ne sont pas vérifiés à la compilation : `1 + "a"` est une erreur d'exécution.
- Dans les calculs, `vrai` et `faux` se comportent comme `1` et `0` (hérité de Python) ; il vaut mieux ne pas s'en servir ainsi.
- Une fonction ne peut appeler que des fonctions déclarées **avant** elle (ou elle-même) : pas de récursion croisée.
- Le formateur (`fmt`) ne conserve pas les commentaires.

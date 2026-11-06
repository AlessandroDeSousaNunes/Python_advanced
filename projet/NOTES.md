# Compte rendu d'essai : apprendre Plume par le serveur MCP

Tâche : afficher la table de multiplication de 7, de 1 à 10, sous la forme `7 x 3 = 21`.

## 0. Disponibilité du serveur

Au démarrage, le serveur `plume` était encore « en cours de connexion ». Une recherche d'outils a attendu sa connexion, puis a trouvé six outils : `check`, `format`, `parse`, `run`, `tokenize`, `transpile`. Les instructions du serveur (texte envoyé à la connexion) indiquaient la démarche à suivre : spécification, puis exemple, puis `check`, puis `run`.

**Le prompt `ecrire_programme` ne m'était pas accessible.** Mon client ne présente pas les prompts MCP comme des outils que je peux appeler. J'ai donc suivi la même démarche à la main, comme le prévoyait la consigne.

## 1. Resources lues et outils appelés, dans l'ordre

1. `ListMcpResources` (serveur `plume`) : il liste deux resources, `plume://specification` et `plume://exemples`.
2. Lecture de `plume://specification`.
3. Lecture de `plume://exemples` (la liste des 5 exemples).
4. Lecture de `plume://exemples/03_boucles`.
5. Outil `check` sur la version 1.
6. Outil `run` sur la version 1.
7. Outil `format` sur la version 1.

## 2. Versions essayées

### Version 1 (seule version)

```
# Table de multiplication de 7
soit i = 1;
tantque i <= 10 {
    affiche 7, "x", i, "=", 7 * i;
    i = i + 1;
}
```

- `check` → `{"ok": true, "erreurs": []}`, aucune erreur.
- `run` → `statut: "ok"`, aucune erreur, durée 0,159 s, sortie conforme (voir plus bas).

## 3. Nombre d'allers-retours

**Un seul** : le premier programme est passé à `check` puis à `run` sans erreur. Il n'y a eu aucune correction.

## 4. Programme final (mis en forme par `format`)

```
soit i = 1;
tantque i <= 10 {
    affiche 7, "x", i, "=", 7 * i;
    i = i + 1;
}
```

`format` a répondu `modifie: true` avec l'avertissement « les commentaires (#) ont été supprimés ». C'était le seul changement : mon code avait déjà l'indentation attendue.

### Sortie exacte de `run`

```
7 x 1 = 7
7 x 2 = 14
7 x 3 = 21
7 x 4 = 28
7 x 5 = 35
7 x 6 = 42
7 x 7 = 49
7 x 8 = 56
7 x 9 = 63
7 x 10 = 70
```

## 5. Avis

### Ce qui m'a aidé

- **La spécification est complète et compacte.** Elle donne un programme d'accueil, le lexique, une grammaire EBNF, les priorités des opérateurs, la sémantique et les limites. Avec elle seule, j'aurais pu écrire le programme.
- **Une phrase m'a donné la solution directement** : « `affiche a, b, c;` affiche les valeurs séparées par une espace ». Grâce à elle, `affiche 7, "x", i, "=", 7 * i;` produit exactement `7 x 3 = 21`, sans concaténation ni appel à `texte()`.
- **L'exemple `03_boucles` correspond exactement au besoin**, un compteur avec `tantque`. La table des exemples dans la spécification (« ce qu'il montre ») permet de choisir le bon exemple sans tous les lire.
- **Les instructions envoyées à la connexion** résument la démarche en deux phrases. C'est utile pour une IA qui ne sait pas par où commencer.
- **Les réponses des outils sont en JSON clair** (`ok`, `erreurs`, `statut`, `sortie`, `duree`). L'avertissement de `format` sur les commentaires est appréciable.

### Ce qui manquait ou était peu clair

- **Le prompt `ecrire_programme` est invisible** pour un client qui n'expose pas les prompts MCP comme outils, ce qui est le cas de Claude Code. Je suggère d'en reprendre le contenu dans les instructions du serveur, ou dans une resource du type `plume://demarche`, pour qu'aucun client ne le perde.
- **Je n'ai vu aucun message d'erreur.** Le programme était correct du premier coup, donc je ne peux pas juger la clarté des messages de `check` et `run`. Un petit exemple d'erreur dans la spécification aiderait : une réponse `check` avec `ligne` et `colonne` montrerait à l'avance le format des erreurs.
- **Le formateur a deux noms.** La spécification parle du « formateur (`fmt`) », alors que l'outil s'appelle `format` et que `transpile` propose un backend `formateur`. Le lien entre ces trois noms n'est pas évident.
- **L'espace après chaque valeur n'est pas précisée** : la spécification ne dit pas si `affiche` en ajoute une en fin de ligne. Je l'ai vérifié sur la sortie : il n'y en a pas. Il serait bon de l'écrire.
- **La spécification pourrait mentionner les outils.** Par exemple, une phrase indiquant que `check` fait toutes les vérifications de compilation et que `run` appelle `check` lui-même. Cette dernière information n'apparaît que dans la description de `run`.
- **Détail : le paramètre `delai` de `run`** est en secondes, avec une valeur par défaut de 2. C'est clair dans le schéma, rien à redire.

# Première proposition — Inégalités de mobilité des passeports, 2006–2025

## Intention et livrables

**Question : comment les inégalités de mobilité associées aux passeports ont-elles évolué entre 2006 et 2025, selon les pays et les régions ?**

Le prototype s’adresse aux analystes en relations internationales, journalistes de données et décideurs publics. Il propose un parcours **monde → régions → pays → conditions d’entrée** : distinguer l’évolution générale de l’accès, les écarts entre et au sein des régions, les trajectoires nationales contrastées et la signification administrative du score.

- Script : `prototype_ia.py`, en pandas et Plotly.
- Résultat : `livrables\proposition_ia.html`, ouvrable directement dans un navigateur.
- Tests ciblés : `tests\test_prototype_ia.py`.
- Sources : les deux CSV locaux ; définitions et provenance examinées dans `readme.md`.

Il s’agit d’une **page HTML autonome comportant exactement quatre figures Plotly**, certaines avec plusieurs panneaux. Elle ne nécessite ni serveur, ni API, ni CDN. Les survols et légendes de Plotly fonctionnent localement ; aucun filtre partagé, sélection coordonnée ou application Streamlit n’est introduit dans cette itération. Les tableaux détaillés rendent les valeurs accessibles sans survol.

## 1. Examen préalable des données

Les choix ci-dessous ont été arrêtés **après lecture des CSV**, et non à partir des seuls noms de colonnes.

### Historique `rank_by_year.csv`

| Contrôle | Résultat observé |
|---|---|
| Dimensions | 3 950 lignes, 6 colonnes |
| Unité | Un passeport identifié par `code`, une année |
| Couverture | 199 codes distincts, 2006 à 2025 |
| Régions | 7 catégories de la source |
| Doublons `code, year` | 0 |
| Cellules vides / valeurs manquantes explicites | 0 avec une lecture préservant les codes |
| Identité | Un seul libellé de pays et une seule région par code sur la période |
| Scores bruts | De 0 à 194 |
| Rangs | De 1 à 116 ; présence d’ex æquo |

**Attention à la Namibie :** son code est `NA`. La lecture utilise `keep_default_na=False` pour éviter que pandas le transforme en valeur manquante.

La couverture et les scores nuls ne sont pas uniformes :

| Année | Lignes présentes | Scores nuls | Scores positifs exploitables |
|---|---:|---:|---:|
| 2006 | 185 | 2 | 183 |
| 2007 | 185 | 185 | 0 |
| 2008 | 198 | 15 | 183 |
| 2009 | 198 | 198 | 0 |
| 2010 | 199 | 10 | 189 |
| 2011 | 199 | 6 | 193 |
| 2012 | 199 | 6 | 193 |
| 2013 | 199 | 5 | 194 |
| 2014 | 199 | 5 | 194 |
| 2015 | 199 | 5 | 194 |
| 2016 | 199 | 5 | 194 |
| 2017 | 199 | 5 | 194 |
| 2018–2025, chaque année | 199 | 0 | 199 |

Au total, **447 scores sont nuls**, alors que les rangs de ces lignes sont renseignés. En particulier, tous les passeports présents ont un score nul en 2007 et en 2009. Par exemple, la France a un score de 128 en 2006, 0 en 2007, 152 en 2008 et 0 en 2009, avec des rangs positifs durant ces quatre années. Cela rend une interprétation littérale comme « aucune destination accessible » particulièrement douteuse.

**Décision prudente, à confirmer auprès de la source : considérer tous les scores nuls comme indisponibles.** Le CSV et son dictionnaire ne prouvent pas explicitement que zéro est un code de donnée manquante : il s’agit d’une hypothèse analytique déclarée, pas d’une correction certaine. Aucune explication politique n’est attribuée à ces valeurs.

### Instantané `country_lists.csv`

- 199 lignes et 7 colonnes ; un code unique par ligne.
- Les codes et noms de passeports correspondent à ceux de l’historique.
- Les **995 cellules JSON** des cinq catégories utilisent l’enveloppe `[[{"code": "...", "name": "..."}]]`. Il faut retirer la liste extérieure avant de compter les destinations.
- Aucun JSON invalide, code de destination dupliqué au sein d’une catégorie ou chevauchement entre catégories pour un même passeport n’a été trouvé.
- L’union de toutes les listes contient **227 codes de destination distincts**. Ce nombre ne doit pas être confondu avec les 199 passeports étudiés.
- La somme des cinq listes vaut **226 pour 198 passeports**, et **225 pour Israel**. Le prototype conserve cette différence sans tenter de l’expliquer.
- La somme `visa_free_access + visa_on_arrival + electronic_travel_authorisation` reproduit `visa_free_count` de 2025 pour **199 passeports sur 199**.
- Le fichier n’a **aucune colonne temporelle**. La concordance des scores ne démontre ni une date exacte de collecte, ni une collecte simultanée des deux fichiers.

## 2. Traitements et périmètre de comparaison

### Mesure principale

Le score `visa_free_count` désigne l’accès **au sens Henley**, pas exclusivement une exemption de visa. Selon la documentation locale, sont comptés les accès sans visa, certains visas à l’arrivée et les autorisations électroniques de voyage (ETA). Les visas requis et les visas électroniques nécessitant une approbation préalable ne sont pas comptés. « Compté dans le score » n’équivaut donc pas à « sans formalité ».

Une destination n’est pas nécessairement un État souverain. Un passeport est l’unité statistique : le prototype ne mesure pas directement la mobilité des habitants, ne pondère pas par population et ne mesure ni flux de voyageurs, ni coût du déplacement.

### Comparaisons historiques à composition constante

1. Contrôler colonnes, identifiants, nombres entiers, absence de doublons et stabilité des régions.
2. Conserver les données brutes et créer en mémoire une colonne `score`, où les seuls zéros deviennent manquants.
3. Identifier les années ayant au moins un score positif : **18 années**, hors 2007 et 2009.
4. Retenir les codes disposant d’un score positif à chacune de ces 18 années : **183 passeports**, soit 3 294 scores exploitables dans le panel.
5. Réintroduire toutes les années 2006–2025 dans les axes et tables. Les valeurs de 2007 et 2009 restent manquantes ; aucune interpolation, propagation de valeur ou reconstruction depuis le rang.
6. Calculer médianes et quantiles avec l’interpolation linéaire de pandas. Les quantiles peuvent ainsi être décimaux, même si les scores sont entiers.

Les **16 exclusions** sont : Cape Verde Islands, Chad, Comoro Islands, Congo (Dem. Rep.), Cote d'Ivoire, Egypt, Kosovo, North Macedonia, Micronesia, Moldova, Montenegro, Palau Islands, South Sudan, Timor-Leste, Vatican City et Palestinian Territory. Elles résultent d’une absence de ligne et/ou de scores nuls sur au moins une année exploitable. Elles ne doivent pas être interprétées comme des pays sans mobilité.

Les trois premières figures utilisent ce même panel. Il évite de confondre évolution et entrée de nouveaux codes, mais introduit un **biais de sélection vers les séries les mieux renseignées**. Le HTML expose les exclusions, la couverture annuelle et une comparaison avec tous les scores disponibles.

### Instantané des conditions d’entrée

Le script décode les JSON avec `json.loads`, contrôle les objets et les doublons, compte les destinations puis joint les régions par `code`, avec validation de l’unicité de la jointure. Il calcule des **moyennes de nombres de destinations**, sur les 199 passeports de l’instantané, sans imposer un total de 226 et sans les transformer en pourcentages.

Il n’utilise pas l’univers actuel des destinations comme dénominateur de l’historique : cet univers n’est pas documenté année par année.

## 3. Les quatre graphiques proposés

### Figure Monde — Distribution annuelle et écart absolu

**Question :** une hausse de l’accès médian s’accompagne-t-elle d’une réduction des écarts ?

**Message observé dans le panel :** entre 2006 et 2025, la médiane passe de **46 à 100 destinations**. Le dixième percentile passe de **19 à 47**, le quatre-vingt-dixième de **124,6 à 187** ; l’écart `P90 − P10` augmente de **105,6 à 140 destinations**.

La conclusion dépend toutefois de la définition de l’inégalité : le rapport `P90 / P10` **diminue de 6,56 à 3,98**. Le texte introductif présente les deux mesures. Une hausse de l’écart absolu ne permet donc pas d’affirmer que toutes les mesures d’inégalité augmentent.

**Encodages réellement implémentés :**

- Axe horizontal : année.
- Panneau supérieur : médiane en trait et points, P10 et P90 en pointillés, rubans P10–P90 et P25–P75.
- Panneau inférieur : courbe `P90 − P10`, en destinations, avec son axe propre commençant à zéro ; pas de double axe superposé.
- Bandes grises et interruption des courbes en 2007 et 2009.
- Rubans segmentés pour ne pas relier les périodes séparées par des trous. Des segments verticaux montrent les intervalles aux années isolées 2006 et 2008.
- Rapport relatif indiqué dans le message, la synthèse et le tableau annuel, sans le superposer à une échelle en destinations.

**Limites :** les rubans représentent une dispersion empirique, pas un intervalle de confiance. Les pays situés à P10 et P90 peuvent changer d’une année à l’autre ; l’indicateur ne suit donc pas un groupe permanent de pays « pauvres » ou « riches » en mobilité. Il masque aussi les extrêmes. La variation du nombre de destinations potentiellement évaluées reste inconnue.

### Figure Régions — Petits multiples des médianes et dispersions

**Question :** comment les niveaux et les disparités internes évoluent-ils selon les régions ?

**Message :** les régions présentent des niveaux différents ; les rubans permettent de ne pas réduire chaque groupe à sa médiane. En 2025, les médianes régionales du panel s’étendent de **59 à 183,5 destinations**.

| Région source, libellé affiché | Effectif constant | Médiane 2006 | Médiane 2025 |
|---|---:|---:|---:|
| AFRICA, Afrique | 47 | 35 | 59 |
| AMERICAS, Amériques | 22 | 82 | 139 |
| ASIA, Asie | 31 | 27 | 63 |
| CARIBBEAN, Caraïbes | 13 | 62 | 147 |
| EUROPE, Europe | 44 | 108,5 | 183,5 |
| MIDDLE EAST, Moyen-Orient | 14 | 27 | 78 |
| OCEANIA, Océanie | 12 | 48 | 127,5 |

**Encodages :** sept panneaux, mêmes axes verticaux **0–200 destinations**, abscisses temporelles, médiane en trait et points, ruban P25–P75 ; effectif inscrit dans chaque titre. Couleurs de régions stables et reprises dans la figure Pays. Les trous temporels restent visibles. Les intervalles des années isolées sont matérialisés verticalement.

**Limites :** une région n’est pas un bloc homogène, particulièrement avec des tailles de groupe différentes. L’écart interquartile ne représente pas tous les pays. Les catégories sont reprises telles quelles — notamment « Caraïbes » séparées des « Amériques » — sans prétendre à une géographie universelle. Leur stabilité dans le fichier ne garantit pas une reconstitution historiquement exacte des appartenances territoriales.

### Figure Pays — Score initial et variation entre les deux bornes

**Question :** quels passeports connaissent les plus fortes variations, et de quel niveau partaient-ils ?

**Message observé :** parmi les 183 passeports appariés, **182 progressent, 1 recule et aucun n’est stable**. United Arab Emirates passe de **35 à 184**, soit **+149 destinations** ; Bolivia de **83 à 78**, soit **−5**. Ce sont les variations maximale et minimale du panel, pas une sélection éditoriale arbitraire.

**Encodages :**

- Abscisse : score de 2006.
- Ordonnée : score de 2025 moins score de 2006, en destinations.
- Un point de taille constante par passeport ; couleur **et forme** pour la région.
- Ligne horizontale à zéro pour distinguer gains et pertes.
- Quatre règles de nomination : gain maximal, gain minimal, score 2025 maximal et score 2025 minimal. Elles désignent ici United Arab Emirates, Bolivia, Singapore et Afghanistan.
- Survol : nom, code, région, deux scores, variation et rangs source. Tous les pays du panel figurent dans une table triée par gain.

**Limites :** les deux bornes masquent la forme du parcours. Le score initial intervient dans le calcul du gain : une structure dans ce nuage ne démontre pas une convergence ou divergence causale. Les chevauchements de points peuvent masquer des passeports ; les effectifs et la table complète limitent cette perte d’information. Les 16 exclusions du panel ne sont pas classées artificiellement.

Le rang reste secondaire : c’est une position ordinale, dépendant aussi des autres passeports et des ex æquo. Une perte de rang n’implique pas nécessairement une perte de destinations. Aucun classement historique n’est recalculé à partir des scores incomplets.

### Figure Conditions d’entrée — Composition régionale de l’instantané

**Question :** que recouvre concrètement l’accès associé aux passeports ?

**Message :** le score additionne des modalités distinctes, dont certaines comportent encore des démarches. Dans l’instantané, la moyenne des destinations **strictement sans visa** est par exemple de **123,43 en Europe** et **37,07 en Afrique**. Ces moyennes portent sur tous les passeports de chaque région et ne sont pas les médianes du panel historique.

**Encodages :**

- Une barre horizontale empilée par région ; longueur = somme des nombres moyens de destinations.
- Cinq segments : sans visa, visa à l’arrivée, ETA, visa en ligne, visa requis.
- Les trois catégories comptées dans le score utilisent une famille de couleurs turquoise/bleu clair ; les deux autres, ocre et bleu foncé.
- La légende suit le même ordre que les segments, de gauche à droite.
- Ordre régional décroissant de la somme moyenne des trois catégories comptées dans le score.
- Effectifs inscrits sur les catégories de l’axe ; moyennes arrondies dans les segments suffisamment larges et valeurs détaillées au survol/dans la table.

**Limites :** c’est un **instantané sans année explicitement renseignée**, pas un graphique d’évolution. Les moyennes régionales cachent des écarts entre pays ; le HTML fournit donc aussi les comptages individuels des 199 passeports. Les segments ne sont pas des pourcentages, leur somme peut différer légèrement selon les régions et ne doit pas être forcée à 226. L’ordre des modalités ne prétend pas mesurer leur coût ou leur difficulté. Les catégories actuelles ne sont jamais appliquées rétrospectivement.

## 4. Sensibilité et précautions transversales

Une comparaison des bornes est incluse dans le HTML :

| Échantillon | Année | n | Médiane | P90 − P10 | P90 / P10 |
|---|---:|---:|---:|---:|---:|
| Panel constant | 2006 | 183 | 46 | 105,6 | 6,56 |
| Panel constant | 2025 | 183 | 100 | 140,0 | 3,98 |
| Tous scores exploitables | 2006 | 183 | 46 | 105,6 | 6,56 |
| Tous scores exploitables | 2025 | 199 | 94 | 141,2 | 4,14 |

Sur ces fichiers, le sens des évolutions entre les bornes reste le même pour ces deux échantillons, mais les niveaux diffèrent. Ce contrôle de composition **ne valide pas** l’hypothèse concernant les zéros et ne règle pas les changements possibles de méthodologie ou d’univers des destinations.

Le prototype ne propose aucune explication causale : ni diplomatie, ni conflit, ni pandémie, ni revenu ne sont identifiés comme causes par ces seuls fichiers. Toute analyse explicative nécessiterait des données supplémentaires, un modèle et une stratégie d’identification adaptés.

La date TidyTuesday **2025-09-09** désigne la publication du jeu de données. Les CSV ne permettent pas de dater précisément chaque relevé, ni de traiter 2025 comme une observation de fin d’année.

## 5. Présentation et accès aux informations

La page adopte une palette froide de dossier analytique : fond bleu pâle `#EDF1F9`, encre `#17324D`, accent turquoise `#007D79`, avertissements ocres `#A65A16`, texte secondaire `#65758B`, surfaces blanches. Les titres utilisent Bahnschrift avec replis système, le texte Segoe UI/Arial et les libellés techniques Consolas ; aucune police n’est téléchargée.

Le repère visuel principal est un bloc **« passage 2006 → 2025 »** présentant ensemble médiane, écart absolu et rapport relatif. L’avertissement sur les zéros précède les graphiques. Les panneaux régionaux remplacent une superposition de sept courbes ; une carte n’est pas retenue ici, car la surface géographique n’est pas la mesure étudiée et aucune ressource cartographique distante n’est nécessaire.

Chaque figure est accompagnée d’un message chiffré, de ses encodages et de ses limites. Les tables HTML, les zones de défilement et les sections dépliables sont accessibles au clavier. Le défilement animé respecte la préférence de mouvement réduit. Sur écran étroit, les graphiques conservent une largeur minimale de 780 pixels et se font défiler horizontalement : c’est un compromis explicite de cette première version, pas une interface mobile optimisée. Les libellés de pays restent ceux de la source pour faciliter les rapprochements.

L’interactivité coordonnée du produit final est laissée ouverte : sélection d’un pays dans plusieurs vues, filtres de période/région et comparaison d’échantillons devront conserver les mêmes définitions, rendre les effectifs visibles et ne pas combler les trous temporels.

## 6. Reproduction et vérification

Depuis le dossier du projet, sous PowerShell :

```powershell
# Si les dépendances de l'environnement ne sont pas encore installées :
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# Génération locale ; les chemins par défaut sont relatifs au script :
.\.venv\Scripts\python.exe prototype_ia.py

# Contrôles ciblés :
.\.venv\Scripts\python.exe -m pytest tests\test_prototype_ia.py -q -p no:cacheprovider
```

Les deux dépendances utilisées par le script sont pandas et Plotly ; Streamlit figure déjà dans les dépendances du projet mais n’est pas utilisé par ce prototype. `pytest` figure dans `requirements-dev.txt`, à installer si nécessaire pour les tests. La génération et l’ouverture du HTML ne téléchargent rien une fois ces dépendances présentes.

Le script accepte aussi `--data-dir` et `--output`. Il n’effectue aucune requête et écrit seulement le HTML demandé. Plotly.js est embarqué **une seule fois** ; pas de police, image ou feuille de style distante. Une politique de sécurité embarquée interdit notamment les connexions réseau. Les empreintes SHA-256 des CSV figurent dans le HTML et sont comparées pendant la génération.

**Versions vérifiées :** Python 3.14.6, pandas 3.0.5, Plotly 6.9.0.

Les tests couvrent les valeurs observées, le code `NA`, les zéros, la constance du panel, la sensibilité à la composition, les différences entre bornes, les JSON imbriqués/vides/invalides, les doublons, les chevauchements, les totaux des listes, la segmentation des rubans, les échelles régionales et la présence des quatre figures sans ressource externe. L’exécution ciblée passe **19 tests**.

Le HTML a également été ouvert directement en `file://` dans Chromium avec l’émulation réseau **Offline**, sans requête HTTP/HTTPS et sans erreur de console après rechargement. Les quatre figures, leurs tables et un survol de pays ont été vérifiés. À 390 pixels de largeur, la page ne déborde pas : seuls les graphiques disposent du défilement horizontal annoncé. Le rendu des graphiques a aussi été contrôlé à 1 440 pixels.

Empreintes des sources examinées, conservées inchangées :

```text
rank_by_year.csv
e1551391b6ff06c31e84d4482191c71a30be5df7a3d670674cd32b265275b5af

country_lists.csv
68775a366fd4192514a6dd1a701d6faeb7f8bfcefd80e9d92d31ce4981e7b653
```

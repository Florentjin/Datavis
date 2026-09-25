# Registre critique : données, IA et encodages

**Statut : analyse et rédaction assistées par IA, à discuter et valider par les
quatre membres.** Les références aux notions du cours sont conceptuelles :
les pages et supports précis devront être ajoutés par le groupe.

## Deux matériaux à ne pas confondre

L'image WhatsApp constitue une trace historique de quatre graphiques. Son prompt
et son code ne sont pas disponibles. Les critiques H1 à H5 ci-dessous portent
sur cette image et sur les CSV, pas sur un dialogue reconstitué.

La nouvelle itération possède un prompt effectivement soumis
(`prompt_iteration_01.md`), une réponse conservée (`reponse_iteration_01.md`)
et un script autonome (`prototype_ia.py`). Elle doit être jugée sur ses choix
réels, y compris les bons choix ; aucune erreur n'a été demandée artificiellement.

## Problèmes de la trace historique

| Réf. | Observation étayée | Décision | Justification et effet |
|---|---|---|---|
| H1 | Les séries s'effondrent à zéro en 2007/2009 ; les 383 observations de ces deux années ont un score nul et un rang renseigné. | Exclure ces scores de l'analyse, maintenir les années et interrompre les courbes. | Intégrité de la représentation : une valeur non interprétable ne doit pas devenir un événement. `connectgaps=False` avec calendrier complet ; aucun lissage. |
| H2 | Le classement des gains attribue 128 destinations au Monténégro, dont le score 2006 est nul. | Calculer les variations seulement sur les paires de scores exploitables. | Comparabilité et traçabilité : pas de variation valide à partir d'une base non interprétable. |
| H3 | Les extrêmes sont montrés comme un classement de trajectoires favorables. | Présenter aussi les cinq variations les plus faibles. | Limiter la sélection d'exemples qui favorise une seule histoire ; un gain faible ne sera pas appelé déclin. |
| H4 | Les couleurs attribuées aux régions ne sont pas cohérentes entre certaines vues. | Utiliser une correspondance région-couleur partagée. | Cohérence de l'encodage et réduction de la charge de réapprentissage ; noms et styles complètent la couleur. |
| H5 | Six courbes et des noms de régions inclinés rendent la lecture dense. | Quatre pays en focus au maximum, libellés lisibles, boxplots horizontaux et navigation par tâche. | Charge cognitive et hiérarchie visuelle : conserver le contexte sans afficher tous les détails simultanément. |

Le fichier contient **447 scores nuls au total**, dont 64 hors de 2007/2009.
La source ne les qualifie pas explicitement de manquants. Le produit parle
d'anomalies présumées, conserve le brut et rend les exclusions consultables.
Ce statut est une limite, pas une découverte certifiée de la méthode Henley.

## Décisions analytiques du produit final

| Réf. | Arbitrage | Motif et contrepartie |
|---|---|---|
| A1 | Panel commun de 183 passeports pour 2006–2025. | Évite d'attribuer au temps un changement de composition du panel. Exclut 16 passeports : les raisons sont consultables. |
| A2 | Score et rang séparés, avec basculement exclusif dans les trajectoires. | Les États-Unis gagnent 52 destinations tout en passant de 1 à 10. Un double axe créerait une superposition ambiguë ; le rang reste mondial après filtrage. |
| A3 | P90–P10 comme indicateur explicite de dispersion absolue. | Moins dépendant d'un seul extrême que min–max. Il ne résume ni toutes les inégalités, ni les rapports relatifs, ni la distribution de la population. |
| A4 | Région selon Henley et poids identique par passeport. | Reproductible avec les variables disponibles ; aucune pondération démographique ou géographie universelle n'est prétendue. |
| A5 | Pas de causalité géopolitique automatique. | Les données montrent une évolution mais ne contrôlent aucun facteur explicatif. Le contexte historique exige des sources supplémentaires. |
| A6 | Code `NA` explicitement conservé. | pandas peut confondre la Namibie avec une valeur absente ; une jointure incorrecte supprimerait des observations réelles. |
| A7 | Usage de `country_lists` limité à la fiche et au contrôle du score 2025. | Ce fichier n'a pas d'année. Sa projection rétroactive inventerait un historique des régimes. La relation Israël–Maldives absente reste inconnue. |

## Décisions d'encodage et d'ergonomie

| Vue | Choix retenu | Théorie et compromis |
|---|---|---|
| Distributions | Boxplots horizontaux, deux dates, mêmes échelles et effectifs. | Position sur une échelle commune pour les médianes ; dispersion visible plutôt qu'une moyenne seule. Le fonctionnement des moustaches doit être expliqué. |
| Trajectoires | Axe temporel réel, trous, couleurs régionales, styles de ligne et marqueurs. | Continuité réservée aux observations consécutives. Les points isolés doivent rester visibles. Quatre séries limitent les croisements et la recherche en légende. |
| Recompositions | Nuage de taille constante, axes identiques, référence d'égalité. | Position pour comparer deux mesures quantitatives. L'aire des points n'ajoute pas une variable arbitraire ; le rapport 1:1 évite de déformer les gains visuels. |
| Variations | Barres horizontales autour de zéro, valeurs signées et extrêmes sans doublons. | Longueur proportionnelle à une variation ; traitement des valeurs négatives sans troncature trompeuse. Les titres reflètent les signes réellement présents. |
| Navigation | Quatre onglets et filtres communs, table accessible, export CSV. | Une tâche par vue et une largeur suffisante, plutôt qu'une grille de quatre petits graphiques. Le lecteur peut vérifier les valeurs sans dépendre du survol. |

Le nuage et les barres partagent les mêmes données d'extrémité, mais pas la même
tâche : le premier situe la recomposition selon le niveau initial ; les secondes
ordonnent son amplitude. Si une vue ne répondait pas à une tâche distincte,
la supprimer serait préférable à la conserver pour remplir l'écran.

Une carte, un bump chart principal ou un chatbot ont été écartés du périmètre :
ils ne répondent pas mieux aux quatre tâches retenues et détourneraient l'effort
des exigences de méthode et de critique. La couleur régionale n'est jamais
le seul moyen d'identifier les observations.

## Résultats à défendre avec leur périmètre

Sur le panel commun 2006–2025 :

- Émirats arabes unis : 35 → 184, soit +149 destinations.
- États-Unis : 130 → 182, soit +52 ; rang mondial 1 → 10.
- Bolivie : 83 → 78, soit −5 destinations.
- P90–P10 : 105,6 → 140 destinations.
- Médianes : Europe 108,5 → 183,5 ; Afrique 35 → 59.

Ces valeurs ne permettent pas de conclure à une aggravation universelle de
toutes les inégalités. Le constat de hausse concerne les indicateurs absolus
énoncés, sur ce panel, avec les limites de couverture et de définition de la source.

## Audit de la nouvelle proposition et de la restitution

| Réf. | Proposition réellement observée | Arbitrage final |
|---|---|---|
| N1 | La nouvelle IA repère les zéros, protège `NA`, segmente les rubans et utilise un panel historique constant. | Conserver ces précautions. Ne pas lui attribuer les erreurs de la capture historique. Le produit interactif recalcule un panel commun aux deux bornes sélectionnées, et affiche les exclusions. |
| N2 | La figure Monde distingue P90–P10 croissant et P90/P10 décroissant : 6,56 → 3,98 sur le panel initial. | Conserver cette nuance dans la synthèse du dashboard et les tables. Elle empêche de transformer une mesure absolue en conclusion universelle. |
| N3 | Sept petits multiples régionaux et une barre empilée des régimes forment deux vues de la proposition. | Remplacer les petits multiples par une comparaison de distributions aux deux dates pour la tâche retenue ; déplacer les régimes dans une fiche 2025 distincte des filtres historiques. Les segments empilés centraux ne partagent pas tous une même origine. |
| N4 | Le nuage proposé oppose le score initial à sa variation. Le score initial intervient donc aussi dans la variable verticale. | Préférer score initial contre score final, axes identiques et diagonale d'égalité, puis classer les variations dans une vue dédiée. Ne pas inférer de convergence causale à partir de l'un ou l'autre nuage. |
| N5 | Le prototype est autonome, mais sans filtres partagés et avec des figures d'au moins 780 pixels défilant horizontalement. | Conserver l'export comme archive ; ajouter Streamlit, contrôles communs, messages d'exclusion, tables et disposition adaptée aux petites largeurs. |
| N6 | Un brouillon de restitution rédigé avec l'IA indiquait « Bolivie : 82 → 77 », tout en donnant le bon delta −5. | Corriger les niveaux en **83 → 78** après retour aux deux lignes du CSV. Vérifier seulement le delta aurait laissé passer cette erreur. Les assertions portent désormais aussi sur les niveaux. |

La nouvelle proposition et son code ne sont pas réécrits pour leur attribuer
les choix du produit final. Ils restent archivés. Le prompt initial historique
est toujours inconnu ; la nouvelle demande ne le remplace pas rétroactivement.

## Validation humaine à compléter

Le groupe doit discuter les exclusions, la pertinence des tâches, les choix
de focus et les contreparties des graphiques ; renseigner qui valide les
décisions ; citer les supports exacts du cours. Ce registre n'attribue pas
une validation fictive aux étudiants.

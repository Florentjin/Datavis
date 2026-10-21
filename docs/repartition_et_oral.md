# Travail à quatre et défense du projet

Ce document propose une organisation ; il ne prétend pas que les membres ont
déjà exécuté ou validé les tâches indiquées. Le groupe doit renseigner les noms,
discuter les choix et pouvoir expliquer le code avant de remettre le projet.

## Responsabilités

| Rôle | Responsabilité | À savoir défendre |
|---|---|---|
| A — Méthode | `data.py`, `metrics.py`, contrôle des données et résultats | Les 447 zéros, le code Namibie, la cohorte commune, les limites des sources. |
| B — Comparaisons | Distributions et recompositions, lecture des écarts | Boxplot, médiane/quartiles, panel constant, géométrie du nuage et diagonale. |
| C — Interaction | Streamlit, trajectoires et variations | Cohérence des filtres, score/rang, lacunes, zéro des barres et messages. |
| D — Critique | Journal, sources, contre-lecture, support oral | Provenance réelle de l'IA, arbitrages conservés/modifiés/rejetés, charge cognitive. |

Chacun rédige la justification de ses choix et relit une vue qu'il ne pilote pas.
Les quatre membres doivent comprendre le chargement, le sens des variables et
le récit central ; D ne rédige pas seul toute la réflexion.

## Fil conducteur de l'oral

L'énoncé demande 6 à 8 minutes pour le groupe. Construire une démonstration
sélective autour d'un raisonnement, plutôt qu'un inventaire des boutons.

1. **Le problème.** Un passeport ne donne pas les mêmes possibilités d'accès.
   Notre public a besoin de comparer des niveaux, des distributions et des
   trajectoires, sans confondre un score et un classement.
2. **La première difficulté était dans les données.** La capture initiale
   montrait des chutes à zéro en 2007/2009 ; tous les scores de ces années
   sont nuls. Les traiter comme de vrais effondrements aurait créé une histoire
   trompeuse. La source ne certifie pas leur signification : nous les mettons
   à l'écart et montrons les lacunes.
3. **Le constat quantifié.** Sur les 183 passeports comparables, P90–P10 passe
   de 105,6 à 140 destinations. Cela décrit une hausse de dispersion absolue
   pour cette mesure, pas une théorie générale de toutes les inégalités :
   le rapport P90/P10 diminue de 6,56 à 3,98 sur le même panel.
4. **Le contre-exemple utile.** Les États-Unis passent de 130 à 182 destinations,
   mais du rang 1 au rang 10. Basculer score/rang montre pourquoi « déclin »
   est ambigu sans préciser l'indicateur.
5. **La critique qui change un résultat.** Le Monténégro ne figure plus dans
   les gains de 2006–2025 : son score initial nul ne permet pas le calcul.
   Ne pas réparer ce problème aurait conservé un faux gain de 128.
6. **La conclusion et ses limites.** Les niveaux d'accès progressent souvent,
   les positions se recomposent et certaines mesures d'écart augmentent.
   Le dataset ne prouve pas les causes diplomatiques et ne mesure pas les
   voyages réels. L'IA aide à explorer ; ses traitements et ses encodages
   doivent être examinés.

## Démonstration conseillée

Commencer avec la comparaison 2006–2025 et toutes les régions. Montrer les
effectifs et les distributions, puis le cas américain avec le sélecteur
score/rang. Terminer par les variations et l'explication du Monténégro exclu.
Les autres vues restent disponibles pour les questions. Ne pas chercher à
montrer chaque interaction ni à justifier une cause non documentée.

Utiliser `livrables\dashboard.html` ou les captures si l'application ne peut pas
être lancée pendant la soutenance. L'export HTML contient Plotly et fonctionne
hors ligne ; il n'a pas les filtres coordonnés de Streamlit.

## Questions à préparer

| Question possible | Réponse à maîtriser |
|---|---|
| Pourquoi ne pas conserver les zéros ? | Leur structure est suspecte, notamment deux années entièrement nulles avec des rangs renseignés. Nous les signalons et les excluons par prudence, sans affirmer que la source a confirmé leur statut. |
| Pourquoi 183 et non 199 ? | Il faut des scores exploitables aux deux dates. Les statistiques comparatives utilisent exactement le même panel. |
| Pourquoi un boxplot ? | Pour lire la médiane et la dispersion intrarégionale, qu'une moyenne seule masque. |
| Pourquoi deux graphiques sur les mêmes dates ? | Le nuage situe les variations selon le niveau initial ; les barres classent leur amplitude. Ce sont deux tâches différentes. |
| Pourquoi pas une carte ? | La tâche est une comparaison quantitative précise ; l'aire des territoires n'apporte rien et détournerait l'attention. |
| Pourquoi pas un bump chart comme vue principale ? | Un rang est relatif ; il peut masquer un gain réel de destinations. Nous proposons un basculement explicite, sans double axe. |
| L'indice mesure-t-il la liberté réelle de voyager ? | Non : il représente des règles d'accès pour des hypothèses de séjour précises, sans coûts, revenus ou voyages effectifs. |
| Les événements politiques expliquent-ils les courbes ? | Pas avec ces seules données. Une annotation explicative exige d'autres sources et une formulation prudente. |
| Qu'avez-vous réellement conservé de l'IA ? | Consulter le registre et la nouvelle proposition conservée ; distinguer ses décisions des erreurs visibles dans l'image historique. |
| Les régions sont-elles universelles ? | Non, il s'agit du découpage du fournisseur, combinant catégories géographiques et catégories propres à Henley. |

## Avant la remise

- Renseigner les membres et obtenir une validation réelle des arbitrages.
- Ajouter les références exactes des notions vues en cours, sans inventer de
  pages ou de citations.
- Relire le journal de 2 à 3 pages et vérifier que chaque personne peut en
  expliquer au moins une correction.
- Choisir le dépôt ou l'hébergement à remettre. Ne publier aucun secret ni
  l'environnement `.venv`.
- Faire confirmer la séance de soutenance : séance 8 dans le calendrier de
  l'énoncé, séance 7 dans sa liste des livrables.

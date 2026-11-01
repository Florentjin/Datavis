# Registre critique : données, IA et encodages

Registre complet des arbitrages résumés dans le journal de bord
(`docs/journal_de_bord.md`). Auteurs : Raphaël, Florent, Mao, Capucine.
Références au cours : **S** = séance, **d.** = diapositive des supports.

## Deux matériaux à ne pas confondre

L'image WhatsApp (`livrables/captures/trace_historique.jpg`) est une trace historique de quatre graphiques ; son prompt et
son code sont inconnus. Les critiques H1 à H5 portent sur cette image et sur les
CSV, pas sur un dialogue reconstitué.

L'itération 01 possède un prompt réellement soumis (`prompt_iteration_01.md`),
une réponse conservée (`reponse_iteration_01.md`) et un script autonome
(`prototype_ia.py` → `livrables/proposition_ia.html`). Elle est jugée sur ses
choix réels, y compris les bons ; aucune erreur n'a été demandée artificiellement.

## Problèmes de la trace historique

| Réf. | Observation étayée | Décision | Principe du cours |
|---|---|---|---|
| H1 | Les séries s'effondrent à zéro en 2007/2009 ; les 383 observations de ces deux années ont un score nul et un rang renseigné. | Exclure ces scores, garder les années sur l'axe et les signaler « n.d. » sans les relier. | Rendre visibles les manquants (S3 d. 49) |
| H2 | Le classement des gains attribue 128 destinations au Monténégro, dont le score 2006 est nul. | Calculer les variations seulement sur des paires de scores exploitables. | Intégrité de la représentation (S3 d. 40–42) |
| H3 | Seules les trajectoires favorables sont montrées. | Montrer aussi les 5 plus faibles variations (Q3), barres à base zéro. | Tâche top/flop (S4 d. 6) |
| H4 | Couleurs régionales incohérentes d'une vue à l'autre. | Un seul code couleur partagé ; bleu = favorable, orange = défavorable. | Standardiser les codes visuels (S3 d. 25–29) |
| H5 | Six courbes, libellés inclinés, lecture dense. | Une question par écran, libellés horizontaux, 5 à 7 éléments nommés. | Mémoire de travail 5–9 éléments (S2 d. 4) ; charge cognitive (S3 d. 13) |

Le fichier contient **447 scores nuls au total**, dont 64 hors de 2007/2009.
La source ne les qualifie pas explicitement de manquants : le produit parle
d'anomalies présumées et rend les exclusions consultables (encadré « Méthode et
limites » de la page Synthèse). Ce statut est une limite, pas une découverte certifiée.

## Décisions analytiques

| Réf. | Arbitrage | Motif et contrepartie |
|---|---|---|
| A1 | Panel commun de 183 passeports pour 2006–2025 (Q2, Q3). | Évite d'attribuer au temps un changement de composition. Exclut 16 passeports sans score exploitable à l'une des deux dates. |
| A2 | Score seul, sans rang. | Les États-Unis gagnent 52 destinations tout en passant de 1 à 10 : le rang mélange progression propre et progression des autres. |
| A3 | P10, médiane et P90 explicites (Q2). | Moins sensible aux extrêmes que min–max. Ne résume ni les rapports relatifs ni la population concernée. |
| A4 | Régions selon Henley, poids identique par passeport. | Reproductible ; aucune pondération démographique n'est prétendue. |
| A5 | Pas de causalité géopolitique. | Les données décrivent des écarts ; Q6 (r = 0,13) montre justement qu'accueillir n'explique pas la puissance du passeport. |
| A6 | Code `NA` conservé. | pandas confondrait la Namibie avec une valeur absente. |
| A7 | `country_lists.csv` limité à 2025 (Q4–Q8). | Le fichier n'a pas d'année : aucun historique des régimes n'est inventé. Le score Henley compte l'ETA, pas le e-visa. |

## Décisions d'encodage par question

Deux questions analytiques — *qui peut voyager ?* (Q1–Q4, 2006–2025) et
*qui accueille, et à quelles conditions ?* (Q5–Q8, 2025) — déclinées en quatre
tâches distinctes chacune (S4 d. 6). Aucune vue ne répète la tâche d'une autre.

| Vue | Tâche | Choix retenu | Principe du cours |
|---|---|---|---|
| Q1 Répartition | Distribution | Points sur un axe commun, médiane marquée par région, une seule teinte. | Position sur une échelle commune (S2 d. 35) |
| Q2 Évolution | Évolution | Barre P10–P90 par année, médiane en trait noir, 2006 et 2025 en couleur. | Séries temporelles (S4 d. 13–21) ; couleur de mise en évidence (S2 d. 38) |
| Q3 Gagnants/perdants | Classement | 5 + 5 pays, barres à base zéro, recul en orange. | Base zéro (S3 d. 40–42) ; daltonisme : bleu/orange (S2 d. 45–47) |
| Q4 Formalités | Parties d'un tout | Barres 100 %, deux familles de couleur, total « sans démarche » écrit. | Barres empilées (S5 d. 7–9) |
| Q5 Réciprocité | Parties d'un tout | Même code que Q4, solde écrit. | Standardisation (S3 d. 27) |
| Q6 Accueil/puissance | Corrélation | Nuage en quatre quadrants, autres pays en gris, 7 pays nommés en bleu, r écrit. | Annotation et contexte (S4 d. 11) ; couleur avec intention (S2 d. 48) |
| Q7 Entre régions | Matrice | Carte de chaleur séquentielle, diagonale encadrée, minimum en orange. | Heatmap (S4 d. 22) ; alerte (S2 d. 38) |
| Q8 Clubs | Comparaison | Haltères « vers non-membres / entre membres », moyenne mondiale en repère. | Encodage redondant position + libellé (S3 d. 21–23) |

Une carte choroplèthe, un bump chart et un chatbot ont été écartés : ils ne
servent aucune des huit tâches mieux que les vues retenues. La couleur n'est
jamais le seul moyen d'identifier une observation (valeurs et noms écrits).

## Audit de la proposition IA (itération 01)

| Réf. | Proposition réellement observée | Arbitrage final |
|---|---|---|
| N1 | Repère les zéros, protège `NA`, utilise un panel constant de 183 passeports. | **Conservé.** Ne pas lui attribuer les erreurs de la capture historique. |
| N2 | Distingue P90–P10 croissant (106 → 140) et P90/P10 décroissant (6,56 → 3,98). | **Conservé** dans le texte de Q2 : empêche une conclusion universelle. |
| N3 | P90–P10 encodé deux fois (largeur du ruban + second panneau) ; rubans imbriqués et légende à décoder. | **Modifié** : une barre P10–P90 par année, valeurs écrites (S3 d. 18–23). |
| N4 | *Pays* : score 2006 en X et variation en Y, alors que X entre dans le calcul de Y ; plus de 180 points colorés selon 7 régions. | **Rejeté** : remplacé par le classement 5 + 5 de Q3 (S4 d. 6 ; S2 d. 4). |
| N5 | *Régions* : 7 petits multiples séparés pour comparer 7 médianes. | **Modifié** : un seul axe commun (Q1, S2 d. 35). |
| N6 | *Conditions* : 5 régimes empilés en effectifs, segments centraux sans origine commune. | **Modifié** : barres 100 %, deux familles de couleur, total écrit (Q4, S5 d. 7–9). |
| N7 | Textes d'environ 12 px, aucune valeur écrite, titres descriptifs. | **Modifié** : ≥ 16 px, titre = réponse, sous-titre = clé de lecture (S3 d. 14–15 ; S4 d. 11). |
| N8 | Un brouillon de restitution indiquait « Bolivie : 82 → 77 » avec le bon delta −5. | **Corrigé** en **83 → 78** après retour au CSV ; les tests vérifient aussi les niveaux. |

La proposition et son code ne sont pas réécrits : ils restent archivés tels quels.

## Itération 02 : lisibilité en projection

Une IA de code (GitHub Copilot) a audité les huit vues capturées à 1920×1080
à partir des supports S2 à S5 (rendu final : `livrables/captures/final_q*.png`).

| Constat de l'IA | Arbitrage |
|---|---|
| Textes de 12–14 px illisibles au fond d'une salle. | **Retenu** : 16 px minimum, figures de 780 px ; un test automatique le vérifie. |
| Grilles et légendes redondantes avec les valeurs écrites. | **Retenu** : supprimées (data-ink, S3 d. 18–20). |
| Q3 affichait 10 pays par groupe. | **Retenu** : 5 + 5 par défaut, curseur conservé (S2 d. 4). |
| Message répété trois fois (en-tête, titre, encadré « À retenir »). | **Retenu** : énoncé une seule fois, comme titre du graphique (S3 d. 13). |

## Validation par le groupe

Chaque membre relit et défend les arbitrages de sa partie à l'oral
(`docs/repartition_et_oral.md`) : Raphaël et Florent pour Q1–Q4, Mao et
Capucine pour Q5–Q8. Toute valeur citée doit pouvoir être retrouvée dans
l'application (tableau « Voir les données du graphique ») ou dans les CSV.

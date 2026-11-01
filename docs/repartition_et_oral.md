# Travail à quatre et défense du projet

Groupe : **Raphaël, Florent, Mao, Capucine**. La répartition ci-dessous est une
proposition : chacun doit pouvoir expliquer le code et les arbitrages de sa
partie, et répondre sur l'ensemble du récit.

## Responsabilités

| Membre | Partie | À savoir défendre |
|---|---|---|
| Raphaël | Introduction, Q1 Répartition, Q2 Évolution | Problématique, public, 2 × 4 questions ; axe commun ; barre P10–P90, écart absolu vs rapport ; années « n.d. ». |
| Florent | Q3 Gagnants/perdants, Q4 Formalités, critique des données | Panel de 183, base zéro, Monténégro exclu, Bolivie 83 → 78 ; barres 100 % ; 447 zéros, code `NA`. |
| Mao | Q5 Réciprocité, Q6 Accueil/puissance | Solde de réciprocité, mêmes codes que Q4 ; quadrants, r = 0,13 ≠ causalité. |
| Capucine | Q7 Entre régions, Q8 Clubs, conclusion | Heatmap et diagonale, verrou Afrique → Europe ; haltères, CEDEAO ; limites et rôle de l'IA. |

Code associé : `passport_dashboard/data.py` et `metrics.py` (données, Florent),
`charts.py` (Raphaël pour Q1–Q4, Mao pour Q5–Q8), `questions.py` et `app.py`
(Capucine). Chacun relit une vue qu'il ne présente pas.

## Déroulé de l'oral (≈ 7 min, énoncé : 6 à 8 min)

Montrer **un message par écran** : lire le titre (la réponse), puis pointer
l'élément qui le prouve. Ne pas faire l'inventaire des boutons.

| Temps | Orateur | Écran | Ce qu'on dit |
|---|---|---|---|
| 0:00–0:40 | Raphaël | Accueil | Un passeport n'ouvre pas les mêmes portes. Deux questions : *qui peut voyager ?* (2006–2025) et *qui accueille, et à quelles conditions ?* (2025), quatre vues chacune. |
| 0:40–1:25 | Raphaël | Q1 | Médiane Europe 183 destinations, Afrique 58,5 : la région prédit fortement le passeport. |
| 1:25–2:15 | Raphaël | Q2 | L'écart P10–P90 passe de 106 à 140 destinations… mais le rapport P90/P10 baisse de 6,56 à 3,98 : les plus faibles progressent aussi. Années 2007/2009 non publiées, signalées. |
| 2:15–3:00 | Florent | Q3 | 182 passeports sur 183 progressent ; Émirats +149 ; seule la Bolivie recule (83 → 78). Le Monténégro (+128 dans la capture historique) est exclu : score 2006 nul. |
| 3:00–3:40 | Florent | Q4 | 73 % des destinations sans démarche pour un passeport européen, 28 % pour un africain. Transition vers la partie 2. |
| 3:40–4:25 | Mao | Q5 | Réciprocité : l'Europe reçoit plus qu'elle n'accorde (30 % en sa faveur, 4 % contre) ; l'Afrique l'inverse (12 % / 28 %). |
| 4:25–5:10 | Mao | Q6 | Accueillir largement ne rend pas un passeport puissant : r = 0,13. Quatre quadrants, pays nommés. |
| 5:10–5:55 | Capucine | Q7 | Les 7 régions s'ouvrent davantage à leurs voisins ; le verrou le plus fort : Afrique → Europe, 4 %. |
| 5:55–6:35 | Capucine | Q8 | Les 7 clubs régionaux ouvrent plus entre membres ; record CEDEAO, +75 points. |
| 6:35–7:15 | Capucine | Synthèse (« Méthode et limites ») | Hiérarchie nette mais pas figée. Limites : pas d'historique des régimes, pas de pondération par population, aucune cause démontrée. L'IA a proposé ; nous avons audité (8 arbitrages, journal p. 2). |

**Secours** : si l'application ne démarre pas, projeter
`livrables/captures/final_q1.png` à `final_q8.png` dans le même ordre.
Lancer l'application **avant** la séance (`streamlit run app.py` ou
`docker compose up`) et vérifier la page d'accueil.

## Questions à préparer

| Question possible | Réponse à maîtriser | Qui |
|---|---|---|
| L'énoncé demande 2 à 4 questions, pourquoi 8 vues ? | Deux questions analytiques, chacune déclinée en quatre tâches distinctes (distribution, évolution, classement, parties d'un tout / réciprocité, corrélation, matrice, comparaison). | Raphaël |
| Pourquoi ne pas conserver les zéros ? | Deux années entièrement nulles avec des rangs renseignés : structure suspecte. Nous les excluons et les signalons, sans affirmer que Henley a confirmé leur statut. | Florent |
| Pourquoi 183 et non 199 passeports ? | Il faut un score exploitable en 2006 et en 2025 ; toutes les comparaisons utilisent le même panel. | Florent |
| L'écart se creuse-t-il vraiment ? | En destinations, oui (106 → 140). En proportion, non (6,56 → 3,98). Nous montrons les deux. | Raphaël |
| Pourquoi pas une carte ? | La tâche est une comparaison précise de valeurs ; l'aire des territoires biaiserait la lecture. | Raphaël |
| Pourquoi bleu et orange ? | Lisible par les daltoniens (S2 d. 45–47) ; l'orange est réservé à l'alerte. | Mao |
| Accueillir plus rend-il un passeport plus fort ? | Non : r = 0,13, et une corrélation ne prouverait de toute façon pas une cause. | Mao |
| L'indice mesure-t-il la liberté réelle de voyager ? | Non : des règles d'entrée, sans coûts, revenus, ni voyages effectifs. | Capucine |
| Qu'avez-vous gardé de l'IA ? | Panel constant, protection de `NA`, nuance du rapport P90/P10. Modifié : 5 vues. Rejeté : le nuage score/variation. Voir `docs/audit_ia.md`. | Capucine |
| Les régions sont-elles universelles ? | Non : découpage du fournisseur Henley. | Capucine |

## Avant la remise

- Relire le journal (`livrables/journal_de_bord.pdf`) : chacun doit pouvoir
  expliquer au moins un arbitrage de la page 2.
- Répéter l'oral chronométré au moins deux fois, sur le projecteur si possible.
- Remettre le lien du dépôt GitHub ; ne publier ni secret ni `.venv`.
- Confirmer la séance de soutenance : séance 8 dans le calendrier de l'énoncé,
  séance 7 dans sa liste des livrables.

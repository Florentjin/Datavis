# Contexte et provenance des interactions

## Sujet retenu

Le groupe (Raphaël, Florent, Mao, Capucine) a confirmé le sujet « Inégalités de mobilité internationale :
évolution de la puissance des passeports entre 2006 et 2025, selon les régions
et les pays ». Il comprend quatre membres et a choisi Python, puis
Streamlit + Plotly pour l'application.

Le contexte fourni identifie trois destinataires : analystes en relations
internationales, journalistes de données et décideurs publics. L'intention est
d'étudier les fractures et recompositions de la mobilité, pas de prescrire des
conditions de voyage.

La problématique initialement formulée dans ce contexte était :

> Comment l'écart de puissance et d'accès des passeports s'est-il creusé ou
> reconfiguré à l'échelle régionale et nationale entre 2006 et 2025 ?

La formulation finale retire le présupposé du creusement et organise
l'application en deux questions analytiques de quatre vues chacune :

> Le régime mondial des visas organise-t-il une hiérarchie de la
> mobilité : qui peut circuler, qui accueille, et selon quelles réciprocités ?

1. *Qui peut voyager ?* — Q1 à Q4, scores 2006–2025 (`rank_by_year.csv`).
2. *Qui accueille, et à quelles conditions ?* — Q5 à Q8, listes 2025
   (`country_lists.csv`).

## Ce qui existait réellement

Le dossier contenait deux CSV, leur documentation TidyTuesday, l'énoncé et une
image WhatsApp de quatre graphiques (conservée sous
`livrables/captures/trace_historique.jpg`). Aucun code, notebook, journal de bord ni
historique de prompts n'était présent. Le groupe a indiqué que seule l'image
avait été conservée.

Le texte long fourni ensuite dans la conversation a été décrit par le groupe
comme un contexte. Il n'est donc **pas** attribué rétroactivement à l'IA qui
aurait généré la capture historique. Cette image reste une preuve visuelle,
pas une preuve de dialogue ni une preuve du code utilisé.

## Nouvelle itération identifiable

Le fichier [prompt_iteration_01.md](prompt_iteration_01.md) conserve le prompt
de la nouvelle demande soumise à un assistant. La réponse et le script sont
conservés séparément dans `reponse_iteration_01.md` et `prototype_ia.py`.

Cette nouvelle proposition n'a pas reçu l'instruction d'introduire des erreurs.
L'audit distingue les problèmes de l'image historique des choix réellement
présents dans cette proposition. Une bonne décision de l'IA peut être conservée.

Le produit final Streamlit (huit questions) forme une itération distincte.
Une seconde itération assistée par IA (GitHub Copilot) a porté sur la
lisibilité en projection, à partir des supports du cours. Les arbitrages des
deux itérations, avec les références aux séances, sont documentés dans
[audit_ia.md](audit_ia.md) et résumés dans le journal de bord.

## Sources de méthode

- Énoncé du projet M2 MIAGE présent dans le dossier.
- `readme.md`, section de documentation TidyTuesday conservée.
- [TidyTuesday Henley](https://github.com/rfordatascience/tidytuesday/tree/main/data/2025/2025-09-09).
- [Henley : méthode et définitions](https://www.henleyglobal.com/passport-index/methodology).

La documentation disponible ne définit pas explicitement les scores annuels
nuls comme des absences de données. Leur exclusion est une règle conservatrice
argumentée et signalée, pas une certitude attribuée à Henley.

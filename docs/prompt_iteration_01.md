# Nouvelle itération IA — prompt conservé

Ce prompt est une nouvelle demande réellement soumise à un assistant pendant la
réalisation du projet. Ce n'est pas le prompt historique de l'image WhatsApp,
qui n'a pas été retrouvé. La proposition est conservée séparément du produit final.

## Prompt

Tu es un consultant en analyse et visualisation de données. Propose un premier
prototype Python pour un dashboard analytique du Henley Passport Index,
TidyTuesday 2025-09-09. Le public comprend des analystes en relations
internationales, journalistes de données et décideurs publics. La question est :
comment les inégalités de mobilité associées aux passeports ont-elles évolué
entre 2006 et 2025, selon les pays et les régions ?

Deux fichiers locaux sont disponibles : rank_by_year.csv (code, country, region,
rank, visa_free_count, year) et country_lists.csv (code, country et cinq listes
JSON de destinations : visa_required, visa_online, visa_on_arrival,
visa_free_access, electronic_travel_authorisation).

Produis une première proposition autonome de quatre graphiques complémentaires
en pandas et Plotly, avec messages, encodages et limites. Lis et examine les
données avant de proposer les traitements ; n'invente pas d'observation ni
d'explication causale. Un prototype HTML local statique suffit pour cette
itération, l'interactivité coordonnée viendra dans le produit final.

Conserve ta réponse dans docs/reponse_iteration_01.md et le script dans
prototype_ia.py. Le script doit produire livrables/proposition_ia.html à partir
des CSV locaux, sans API ni CDN. Ne modifie aucun fichier source de données.
N'introduis pas intentionnellement de défaut : l'audit pourra conserver,
modifier ou rejeter des choix réellement présents dans ta proposition.

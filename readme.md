# Passeports : une hiérarchie durable de la mobilité ?

Projet Dataviz & IA — M2 MIAGE, groupe de quatre. Application Python **Streamlit + Plotly**
construite pour être **projetée** pendant l'oral : une page par question, des graphiques figés
(aucun survol nécessaire) qui portent directement leurs valeurs clés.

**Problématique.** Le régime mondial des visas organise-t-il une hiérarchie durable de la
mobilité : qui peut circuler, qui accueille, et selon quelles réciprocités ?

Public : analystes, journalistes et décideurs publics intéressés par les inégalités de mobilité.

## Lancer l'application (ordinateur relié au projecteur)

Depuis ce dossier dans PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ouvrir l'adresse locale indiquée, passer le navigateur en plein écran (F11) et naviguer avec les
flèches ← → en haut à droite (le menu latéral, replié par défaut, reste accessible). Les pages sont
calibrées pour 1920×1080 ; sur un projecteur 1280×720, régler le zoom du navigateur à 67 % (Ctrl −). Les CSV doivent rester à côté de `app.py` ;
aucune connexion Internet n'est nécessaire pendant la présentation.

**Avec Docker** (aucune installation de Python nécessaire) :

```powershell
docker compose up -d --build      # puis ouvrir http://localhost:8501
docker compose down               # arrêter
```

Si le port 8501 est déjà pris : `$env:PORT=8502; docker compose up -d` puis http://localhost:8502.
Construire l'image demande Internet ; la faire **avant** la présentation, l'app tourne ensuite hors ligne.

Environnement de référence : Python **3.14.6**, pandas **3.0.5**, Plotly **6.9.0**,
Streamlit **1.64.0** (`requirements-lock.txt` pour les versions exactes).

## Plan : 2 parties × 4 questions

L'énoncé limite une application interactive à 2–4 questions : l'histoire est donc découpée en
deux parties de quatre questions, chacune avec un graphique et un message à retenir.

| Partie | Question | Graphique |
|---|---|---|
| 1 · Qui peut voyager ? | Q1. Comment la puissance des passeports se répartit-elle entre régions ? | Points par passeport et médiane régionale |
| | Q2. L'écart entre passeports forts et faibles s'est-il creusé depuis 2006 ? | Barres P10–P90 par année et médiane |
| | Q3. Quels passeports ont le plus progressé, lesquels ont stagné ou reculé ? | Barres des plus fortes et plus faibles variations |
| | Q4. Selon sa région, à quelles formalités un voyageur fait-il face ? | Barres empilées par régime d'entrée |
| 2 · Qui accueille, et à quelles conditions ? | Q5. Les ouvertures sont-elles réciproques ou à sens unique ? | Barres empilées de réciprocité et solde |
| | Q6. Les pays qui accueillent le plus ont-ils les passeports les plus puissants ? | Nuage de points à quatre quadrants |
| | Q7. Les régions s'ouvrent-elles davantage à leurs voisins ? | Matrice région × région |
| | Q8. Les grands blocs régionaux forment-ils des « clubs » de mobilité ? | Haltères « entre membres / vers l'extérieur » |

Chaque page contient la question en en-tête, le graphique dont le **titre est la réponse** calculée
à partir des données (dite une seule fois), un guide « Comment lire », une limite et un tableau des données. Une page de synthèse
reprend les huit messages et la méthode.

## Lisibilité en projection (appuyée sur le cours)

- **Taille** : texte de 16 px minimum, valeurs clés à 19–23 px, titres à 28 px ; hauteur unique
  (780 px) pour que question, contrôles et graphique tiennent dans un écran 1080 p sans défiler.
- **Titre-message + sous-titre de lecture** (séance 3, réduire la charge cognitive) : la question
  est posée en en-tête, la réponse est le titre ; le message n'est plus répété trois fois.
- **Couleur intentionnelle** (séance 2) : gris pour le contexte, bleu pour ce dont on parle, orange
  pour l'alerte (recul, minimum) ; palettes bleu/orange adaptées au daltonisme.
- **Pas de double encodage inutile** (séance 3) : Q1 n'a plus 7 teintes de région (la ligne porte
  déjà la région) ; Q2 n'a plus de lignes P10/P90 en plus des barres ; Q6 n'a plus de légende à 7 couleurs.
- **Mémoire de travail 5 à 9 éléments** (séance 2) : Q3 affiche 5 pays par groupe par défaut, Q6 nomme 7 pays.
- **Data-ink ratio** (séance 3) : grilles retirées quand les valeurs sont écrites ; barres à base zéro ;
  années manquantes signalées « n.d. » et jamais reliées.
- Q2 met en avant la première et la dernière année : comparaison avant/après (séance 4).
- 	ests\test_charts.py vérifie la taille minimale du texte et la hauteur de chaque graphique.

## Décisions méthodologiques importantes

- « Sans démarche préalable » = sans visa, visa à l'arrivée ou autorisation électronique (ETA),
  comme le score Henley. Le e-visa et le visa classique sont des démarches préalables.
- Les **447 scores nuls** de la source sont traités comme manquants ; 2007 et 2009 n'ont aucun
  score exploitable et ne sont jamais interpolées.
- Q2 utilise un **panel constant de 183 passeports** mesurés chaque année. L'écart absolu
  P90–P10 grandit (106 → 140) mais le rapport P90/P10 diminue : les deux sont à mentionner.
- `country_lists.csv` est une **photographie 2025** (contrôlée : elle reproduit les scores 2025).
  Q4 à Q8 ne décrivent donc pas d'évolution.
- Q5, Q7 et Q8 se limitent aux relations entre les 199 pays dotés d'un passeport classé.
- Q8 : la composition des organisations (UE, CEDEAO, EAC, Mercosur, CARICOM, ASEAN, CCG) est
  une **donnée externe** (membres 2025, sites officiels), codée dans `passport_dashboard\metrics.py`.
  Elle remplace un graphe de réseau, illisible en projection.
- Le code `NA` de la Namibie est une chaîne valide. Les noms de pays restent ceux de la source.
- Aucune causalité n'est déduite : les graphiques décrivent des écarts.

## Fichiers et livrables

- `app.py` : application Streamlit (accueil, Q1–Q8, synthèse).
- `passport_dashboard\` : `data.py` (chargement et contrôles), `metrics.py` (calculs des 8 questions),
  `charts.py` (graphiques), `story.py` (messages calculés), `questions.py` (textes du récit),
  `theme.py` (charte de projection, palettes adaptées au daltonisme).
- `prototype_ia.py`, `docs\` et `livrables\` : itération IA, audit, journal de bord et préparation de l'oral.
  **À mettre à jour par le groupe** : ces documents décrivent encore l'ancienne version de l'application.

Les documents rédigés avec l'IA doivent être relus et appropriés par le groupe.
Le journal demandé fait 2 à 3 pages ; l'oral, 6 à 8 minutes.

## Contrôles

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
```

Les tests vérifient les chiffres clés de chaque question, l'absence de survol sur les graphiques
et le rendu de chaque page de l'application.

---

# Documentation d'origine — Henley Passport Index Data

This week we are exploring data from the [Henley Passport Index API](api.henleypassportindex.com/api/v3/countries). 
The [Henley Passport Index](https://www.henleyglobal.com/passport-index/about) is produced by Henley & Partners and captures 
the number of countries to which travelers in possession of each passport in the world may enter visa free. 


> For each travel destination, if no visa is required for passport holders from a country or territory, then a score with value = 1 is 
created for that passport. A score with value = 1 is also applied if passport holders can obtain a visa on arrival, a visitor’s permit, 
or an electronic travel authority (ETA) when entering the destination. These visa-types require no pre-departure government approval, 
because of the specific visa-waiver programs in place. Where a visa is required, or where a passport holder has to obtain a government-approved 
electronic visa (e-Visa) before departure, a score with value = 0 is assigned. A score with value = 0 is also assigned if passport 
holders need pre-departure government approval for a visa on arrival, a scenario we do not consider ‘visa-free’. The total score for 
each passport is equal to the number of destinations for which no visa is required (value = 1), under the conditions defined above.

Henley & Partners update the  [Global Passport Index rankings](https://www.henleyglobal.com/passport-index/ranking) each month 
and [changes to the US passport rank](https://edition.cnn.com/2025/07/22/travel/world-most-powerful-passports-july-2025) 
captured media attention recently. 

- Which countries have made the most dramatic improvements in passport power? Which passports have lost the most visa-free access?
- Do countries with stronger trade relationships tend to offer mutual visa-free access?
- Did the COVID-19 pandemic affect passport rankings, particularly for countries that implemented strict border controls?
- How does political instability or economic crisis impact passport strength?

Thank you to [Brenden Smith and Jen Richmond](https://github.com/brendensm @jenrichmond) for curating this week's dataset.

## The Data

```r
# Using R
# Option 1: tidytuesdayR R package 
## install.packages("tidytuesdayR")

tuesdata <- tidytuesdayR::tt_load('2025-09-09')
## OR
tuesdata <- tidytuesdayR::tt_load(2025, week = 36)

country_lists <- tuesdata$country_lists
rank_by_year <- tuesdata$rank_by_year

# Option 2: Read directly from GitHub

country_lists <- readr::read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-09/country_lists.csv')
rank_by_year <- readr::read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-09/rank_by_year.csv')
```

```python
# Using Python
# Option 1: pydytuesday python library
## pip install pydytuesday

import pydytuesday

# Download files from the week, which you can then read in locally
pydytuesday.get_date('2025-09-09')

# Option 2: Read directly from GitHub and assign to an object

country_lists = pandas.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-09/country_lists.csv')
rank_by_year = pandas.read_csv('https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-09/rank_by_year.csv')
```

```julia
# Using Julia
# Option 1: TidierTuesday.jl library
## Pkg.add(url="https://github.com/TidierOrg/TidierTuesday.jl")

using TidierTuesday

# Download files from the week, which you can then read in locally
download_dataset('2025-09-09')

# Option 2: Read directly from GitHub and assign to an object with TidierFiles

country_lists = read_csv("https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-09/country_lists.csv")
rank_by_year = read_csv("https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-09/rank_by_year.csv")

# Option 3: Read directly from Github and assign without Tidier dependencies
country_lists = CSV.read("https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-09/country_lists.csv", DataFrame)
rank_by_year = CSV.read("https://raw.githubusercontent.com/rfordatascience/tidytuesday/main/data/2025/2025-09-09/rank_by_year.csv", DataFrame)
```


## How to Participate

- [Explore the data](https://r4ds.hadley.nz/), watching out for interesting relationships. We would like to emphasize that you should not draw conclusions about **causation** in the data. There are various moderating variables that affect all data, many of which might not have been captured in these datasets. As such, our suggestion is to use the data provided to practice your data tidying and plotting techniques, and to consider for yourself what nuances might underlie these relationships.
- Create a visualization, a model, a [Quarto](https://quarto.org/) report, a [shiny app](https://shiny.posit.co/), or some other piece of data-science-related output, using R, Python, or another programming language.
- [Share your output and the code used to generate it](../../../sharing.md) on social media with the #TidyTuesday hashtag.
- [Submit your own dataset!](../../../pr_instructions.md)

### PydyTuesday: A Posit collaboration with TidyTuesday

- Exploring the TidyTuesday data in Python? Posit has some extra resources for you! Have you tried making a [Quarto dashboard](https://quarto.org/docs/dashboards/)? Find videos and other resources in [Posit's PydyTuesday repo](https://github.com/posit-dev/python-tidytuesday-challenge).
- Share your work with the world using the hashtags #TidyTuesday and #PydyTuesday so that Posit has the chance to highlight your work, too!
- Deploy or share your work however you want! If you'd like a super easy way to publish your work, give [Connect Cloud](https://connect.posit.cloud/) a try.


## Data Dictionary

### `country_lists.csv`

|variable                        |class     |description                           |
|:-------------------------------|:---------|:-------------------------------------|
|code                            |character |Two letter country code. |
|country                         |character |Full country name. |
|visa_required                   |json      |JSON data of code and name of the countries in which you need a traditional visa to enter these destinations, and you need to apply for it in person. |
|visa_online                     |json      |JSON data of code and name of the countries in which you need a visa to enter, but you can apply for it online, and the visa you receive is electronic (pre-departure approval necessary). |
|visa_on_arrival                 |json      |JSON data of code and name of the countries in which you need a visa to enter, but you can apply for and receive the visa upon arrival at the airport (no pre-departure approval necessary). |
|visa_free_access                |json      |JSON data of code and name of the countries in which you do not need a visa to enter. |
|electronic_travel_authorisation |json      |JSON data of code and name of the countries in which you do not need a visa to enter, but you must apply for a digital electronic travel authority before arrival. |

### `rank_by_year.csv`

|variable        |class     |description                           |
|:---------------|:---------|:-------------------------------------|
|code            |character |Two letter country code. |
|country         |character |Full country name. |
|region          |character |Seven category country region. |
|rank            |integer   |Ranking of 'visa_free_count'. |
|visa_free_count |integer   |The number of countries that do not require a visa for the passport holder, or passport holders can obtain a visa on arrival, a visitor’s permit, or an electronic travel authority (ETA) when entering the destination. |
|year            |integer |Year of data. |

## Cleaning Script

```r
library(httr)
library(tidyverse)
library(jsonlite)

# first httr request to get ranking data

req <- GET("api.henleypassportindex.com/api/v3/countries")

parsed <- req$content |> 
  rawToChar() |> 
  fromJSON()

# Data by year was nested into a list. 
# Here we separate them out so that each year has its own row.

rank_by_year <- parsed$countries |> 
  filter(has_data) |> 
  tidyr::unnest_longer(col = data) |> 
  select(code, country, region, data, year = data_id) |> 
  unnest_wider(col = data)


# The data for country_lists is pulled in with multiple httr requests.
# We can run a query for a single country at a time, and we get back a list
# with the country's name and code, and several data frames that show the 
# names and codes of the countries a passport owner has different visa access to. 

# We can define a function to transform the list into a data frame with columns that contain 
# these additional data frames. In order to meet Tidy Tuesday requirements,
# this data was transformed into JSON to be saved into a csv file.

list_to_nested_df <- function(input_list) {
  processed_data <- lapply(input_list, function(x) {
    if(is.data.frame(x)) {
      toJSON(I(list(x)))
    } else {
      x 
    }
  })
  
  df <- data.frame(processed_data)
  
  return(df)
}


country_lists <- data.frame()

for (i in unique(rank_by_year$code)) {
  print(i)
  
  req2 <- GET(paste0("api.henleypassportindex.com/api/v3/visa-single/", i))
  parsed2 <- req2$content |> 
    rawToChar() |> 
    fromJSON()
  
  add <- list_to_nested_df(parsed2)
  country_lists <-  rbind(add, country_lists)
  
  Sys.sleep(2)
}

# After the data is loaded in, you can run the following code to 
# transform the JSON back into nested data frames or tibbles:
#
# country_lists |>
#   mutate(across(c(3:7),
#                 ~map(.x, ~fromJSON(.x)[[1]] |> tibble())))

```

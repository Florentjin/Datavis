# Passeports et inégalités de mobilité

Projet Dataviz & IA — M2 MIAGE, groupe de quatre. Application Python **Streamlit + Plotly**
pour comparer les inégalités d'accès international et les positions des passeports
entre 2006 et 2025. Public : analystes en relations internationales, journalistes
de données et décideurs publics.

## Lancer l'application

Depuis ce dossier dans PowerShell, sans activer de script :

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Ouvrir l'adresse locale indiquée par Streamlit. Les CSV doivent rester à côté de
`app.py`. Aucun compte, clé API ou téléchargement de données n'est nécessaire
pendant l'utilisation.

L'environnement de référence utilise Python **3.14.6**, pandas **3.0.5**,
Plotly **6.9.0** et Streamlit **1.64.0**.
Pour retrouver exactement les dépendances installées, utiliser
`requirements-lock.txt` à la place de `requirements.txt` dans un environnement
Python compatible. Ce fichier inclut aussi les dépendances de développement.

## Lire le dashboard

Les quatre onglets utilisent les mêmes dates et régions ; les passeports en
focus sont mis en évidence sans réduire le panel de comparaison.

| Vue | Question | Graphique |
|---|---|---|
| Niveaux par région | Où en est chaque région, du départ à l'arrivée ? | Médianes reliées : point gris (départ), point coloré (arrivée) |
| Trajectoires | Comment l'accès des passeports suivis a-t-il évolué ? | Courbes annuelles, une couleur par pays, nom au bout de la courbe ; années sans score grisées ; mode rang aux extrémités comme un bump chart |
| Départs et arrivées | D'où partent les pays suivis et où arrivent-ils ? | Diagramme de pente, variation absolue puis relative écrites au milieu |
| Gains et pertes | Qui a le plus gagné, qui a le plus perdu ? | Barres divergentes : bleu = gain, orange = recul |

Les encodages sont volontairement simples et alignés sur le cadre du cours :
position et longueur pour comparer précisément, une couleur par catégorie,
aucun double encodage inutile, valeurs écrites sur les figures pour une
lecture sans survol, densité visuelle limitée à ce que demande chaque tâche.

Les noms de pays restent ceux de la source. Le score est un nombre de
**destinations**, incluant sans visa, visa à l'arrivée et ETA selon Henley.
Il ne faut pas le confondre avec le rang mondial, ni avec des voyages effectués.
Un e-visa à approbation préalable n'est pas inclus.

## Décisions méthodologiques importantes

- Les **447 scores nuls** sont conservés dans les données brutes, mais mis à
  l'écart de l'analyse comme anomalies présumées. Leur signification exacte
  n'est pas certifiée par la documentation disponible.
- Les années 2007 et 2009 n'ont aucun score exploitable. Les courbes sont
  interrompues, jamais interpolées.
- Le code `NA` de la Namibie est une chaîne valide, pas une valeur manquante.
- La comparaison 2006–2025 utilise **183 passeports présents avec un score
  exploitable aux deux dates**. Le Monténégro ne peut pas recevoir un gain
  de 128 destinations fondé sur son score initial nul.
- P90–P10 utilise les quantiles linéaires de pandas sur le panel commun. Les
  poids sont identiques pour les passeports, sans pondération démographique.
- Les rangs restent ceux de la source, même après filtrage.
- `country_lists.csv` est un instantané cohérent avec les scores 2025, sans
  date exacte de collecte. Les régimes ne sont pas un historique. Une relation
  absente reste inconnue (Israël vers les Maldives dans le fichier local).
- Aucune causalité géopolitique n'est déduite des courbes. La couverture
  historique et les règles de l'indice limitent les comparaisons.

## Fichiers et livrables

- `app.py` : application ; `passport_dashboard` : données, calculs, figures et thème.
- `docs\prompt_iteration_01.md` et `docs\reponse_iteration_01.md` :
  nouvelle interaction IA conservée ; ce n'est pas le prompt de la capture historique.
- `prototype_ia.py` : proposition autonome de cette nouvelle itération, séparée
  du produit final.
- `docs\audit_ia.md` : arbitrages et critique ; `docs\journal_de_bord.md` :
  source du journal ; `livrables\journal_de_bord_v1.pdf` : version de lecture.
- `docs\repartition_et_oral.md` : rôles, arguments et préparation à quatre.
- `docs\support_presentation.html` : support de présentation (problématique,
  justification de chaque graphique, lecture des axes) ; `livrables\support_presentation.pdf` :
  version de lecture, 3 pages.
- `livrables\dashboard.html` : export autonome du produit, utile pour la
  démonstration de secours ; les filtres coordonnés restent dans Streamlit.
- `livrables\proposition_ia.html` : proposition IA conservée séparément.

Les documents rédigés avec l'IA doivent être relus et appropriés par le groupe.
Les noms, les références précises au cours et la validation humaine des
arbitrages ne sont pas inventés. L'énoncé situe la soutenance à deux séances
différentes selon ses sections : faire confirmer le jalon par l'enseignant.
Le journal demandé fait 2 à 3 pages ; l'oral, 6 à 8 minutes.

## Reproduire les exports et les contrôles

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe prototype_ia.py
.\.venv\Scripts\python.exe export_dashboard.py
```

Les exports HTML embarquent Plotly et n'utilisent pas de CDN. Les données brutes,
la capture WhatsApp et les fichiers `lesmiserables*.txt` sont laissés intacts.
Les fichiers littéraires ne sont pas utilisés par l'application.
Le dossier n'est pas encore un dépôt partagé : organiser la collaboration et
le mode de remise avant une éventuelle publication, sans inclure `.venv`.

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

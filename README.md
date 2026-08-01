## Le but de ce projet :
Créer un pipeline qui :
lit un fichier CSV (contacts bruts)
nettoie les données
les stocke dans une base SQLite
enrichit les données via une API simulée
envoie des emails (simulation)
gère des relances

Donc, 
Ce pipeline permet de :

nettoyer des données sales
dédupliquer de manière métier
gérer un système de relance automatisé
assurer une logique proche production avec gestion des erreurs et des états

## ENVIRONNEMENT et EXECUTION DU PROJET
Avant de commencer, installer :

Python

Installer Python 3.10 ou plus :
https://www.python.org/downloads/

Vérifier l’installation :

python --version

VS CODE (optionnel mais recommandé)

Télécharger :
https://code.visualstudio.com/

Extensions recommandées :
Python
Pylance
SQLite Viewer
1 - CREATION DU PROJET

Créer un dossier :

jvn-test

Puis structure :
jvn-test/
src/
data/
venv/
pipeline.db
README.md
requirements.txt
2- CREATION ENVIRONNEMENT VIRTUEL

Dans le terminal :

python -m venv venv

Activation :

Windows :
venv\Scripts\activate

Mac/Linux :
source venv/bin/activate

3 - INSTALLATION DES DEPENDANCES

Installer les bibliothèques nécessaires :

pip install pandas
pip install requests
pip install python-dotenv
pip install email-validator
pip install dnspython
pip install tenacity

4 - FICHIER REQUIREMENTS (IMPORTANT)

Créer un fichier requirements.txt :

pandas
requests
python-dotenv
email-validator
dnspython
tenacity

Puis installation automatique :

pip install -r requirements.txt

5 - STRUCTURE DU PROJET

jvn-test/
│
├── data/
│   └── raw_contacts.csv          (données brutes)
│
├── src/
│   ├── main.py                   (orchestration)
│   ├── clean.py                 (nettoyage + validation)
│   ├── db.py                    (base SQLite)
│   ├── enrichment.py            (API + retry)
│   ├── sender.py                (envoi + relances)
│   └── collect.py               (mock API)
│
├── pipeline.db                   (base de données SQLite)
├── pipeline.log                  (logs)
├── README.md                    (documentation projet)
├── requirements.txt             (dépendances Python)
└── venv/                        (environnement virtuel)

5-EXPLICATION DES MODULES
-------------clean.py
normalise les données (SIREN, email)
valide les emails
supprime les emails invalides, génériques et jetables
supprime les doublons (SIREN + email)

--------------db.py
crée la base SQLite
stocke les contacts
empêche les doublons
gère les index pour performance

-------------enrichment.py
appelle une API simulée
gère pagination
retry automatique
backoff exponentiel
limitation de débit

--------------sender.py
gère l’envoi des emails
applique machine à états
gère relances J+3 et J+7
évite les doubles envois (idempotence)
gère bounces et réponses

-------------main.py
orchestre tout le pipeline
lance nettoyage, insertion, enrichissement et envoi

6 - LANCEMENT DU PROJET
Commande principale :  python -m src.main


## EXECUTION
La sortie :
new → queued → sent → followup_1 → followup_2 → replied | bounced | stopped.
Initialise la base SQLite
Nettoie les données CSV
Insère les contacts en base
Lance enrichissement API
Lance moteur d’envoi
Gère les statuts (new, sent, followup...)

## Choix du langage

J’ai choisi **Python** pour ce projet.

C’est plus rapide à mettre en place dans un contexte de test technique et bien adapté pour :

-le traitement de données (CSV, nettoyage, validation)
-les scripts d’automatisation
-les appels API et la gestion de retry

En plus, l’écosystème est simple pour ce type de pipeline.

En production, Node.js ou TypeScript pourrait aussi être un bon choix, surtout si le reste de l’infra est déjà en JavaScript.

## Base de données (justification pourquoi j'ai utilisé SQLite)

J’ai utilisé **SQLite** pour aller plus vite dans le cadre du test.

C’est suffisant ici car :

-le volume de données est faible
-il n’y a pas de forte concurrence
-ça permet de lancer le projet sans installation complexe

En production, je passerais sur **PostgreSQL** pour :

-mieux gérer la concurrence (workers parallèles)
-avoir des verrous transactionnels plus robustes et une meilleure scalabilité du système

## Orchestration

J’utiliserais un **script Python planifié (cron)** pour ce pipeline.

C’est le choix le plus simple et le plus contrôlable dans ce contexte :

- tout reste dans le même code (clean, send, follow-up)
- facile à debug et à versionner
- pas de dépendance externe

n8n serait intéressant pour visualiser les workflows, mais je le trouve moins adapté ici car ça ajoute une couche en plus à maintenir.

À plus grande échelle, n8n ou Make peuvent être utiles, mais ils deviennent vite limités dès qu’on a beaucoup de logique métier ou de cas complexes.



--------------------------------------REPONSES--------------------------------------
## ## ## ## ## ## Partie 1 - Collectes et enrichissement

Pour ce projet, je choisirais plutôt l’API officielle Sirene/INSEE car les données sont plus fiables et déjà bien structurées, ce qui facilite leur traitement.

Deux critères qui me feraient privilégier l’API :

La qualité des données récupérées.
La stabilité de la solution grâce à une documentation claire et un format de réponse standardisé.

J'utiliserais le scraping seulement si les informations dont j'ai besoin ne sont pas disponibles dans l'API.

Le principal risque de l'API officielle est d'être limité par les quotas ou de rencontrer des indisponibilités temporaires.

Le principal risque du scraping est qu'une modification du site web puisse casser le script de collecte.

## ## ## ## ## ## Partie 2 - Nettoyage, dédoublonnage & validation

Nettoyage

Je fais :

nettoyage des SIREN (suppression espaces)
email en minuscule + trim
suppression des sociétés vides ou mal formatées
Validation email

Je vérifie :

format email valide (regex simple)
emails génériques :
contact@, info@, support@, admin@
emails jetables :
mailinator, tempmail
Déduplication

J’utilise comme clé :  SIREN + email

Pourquoi :
le SIREN représente l’entreprise
l’email représente la personne ou le contact
une entreprise peut avoir plusieurs emails valides
Cas du dataset
Formapro : 2 emails différents → 2 contacts possibles
BTP Solutions : 1 email invalide → rejet + 1 conservé
QuickWin : email jetable rejeté + email valide gardé
Rapport

Le pipeline retourne :

nombre total de lignes
nombre gardé
nombre rejeté
raisons du rejet :
email invalide
email générique
email jetable
doublon


#### ## ## ## ##  Partie 3 — Moteur d’envoi & de relance

Machine à états

Le statut suit :

new → queued → sent → followup_1 → followup_2 → replied | hard_bounce | soft_bounce

Fonctionnement
new : contact à traiter
queued : verrou avant envoi
sent : email envoyé
followup_1 : 1ère relance
followup_2 : 2ème relance
replied : réponse reçue
bounce : erreur email
Sélection des contacts

Je sélectionne uniquement :

contacts sans opt-out
contacts non terminés
respect des délais :
3 jours avant relance 1
7 jours avant relance 2
Idempotence

Pour éviter les doublons :

je vérifie le statut avant envoi
je passe par un état "queued"
je bloque les contacts déjà traités
Course critique

Si une réponse arrive pendant l’envoi :

le statut est revérifié avant update final
si “replied”, on stoppe l’envoi
Crash et reprise

Si le programme s’arrête :

la base de données garde le statut
le prochain run reprend là où ça s’est arrêté
## ## ## ### ## ##Partie 4 — Architecture, conformité & délivrabilité

Délivrabilité :
SPF / DKIM / DMARC
warm-up progressif
gestion des bounces

RGPD :
base légale : intérêt légitime B2B
opt-out obligatoire
    distinction :
    contact@ = fonctionnel
    prénom.nom@ = personnel

Orchestration :
Script Python simple (facile à contrôler, mais limité à grande échelle)

Observabilité :
emails envoyés
bounces
taille de la queue
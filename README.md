# Système de Monitoring Énergétique (SME) — Marsa Maroc DEPA
**Marché n° 12/DEPA/2026** — *Direction d’Exploitation au Port d’Agadir*  
**Norme de référence :** ISO 50001:2018 (Management de l'Énergie)  
**Hébergement cible :** Streamlit Community Cloud (Déploiement gratuit en HTTPS depuis GitHub)

---

## 📌 Présentation du Projet

La plateforme SME assure la supervision en temps réel, l'analyse de performance énergétique (IPE/SER) et la gestion des alarmes pour les **6 postes électriques HTA/BT** du Port d'Agadir :

1. **Poste P1 — Quai Nord (Polyvalent)** : Grues mobiles Gottwald, bandes transporteuses d'engrais/clinker, terre-pleins.
2. **Poste P2 — Quai Sud & Cold-Ironing** : Raccordement électrique à quai des navires marchands (6.6 kV / 400 V) et station de pompage.
3. **Poste P3 — Terminal Roulier (Ro-Ro)** : Tirage des remorques et rampes d'accès hydrauliques.
4. **Poste P4 — Terminal à Conteneurs** : Portiques ZPMC (STS-01 & STS-02), cavaliers gerbeurs RTG, parc de conteneurs frigorifiques (*Reefer*).
5. **Poste P5 — Silos & Vracs Agroalimentaires** : Tours élévatrices à grains, trémies d'ensachage mobile.
6. **Poste P6 — Ateliers Centraux & Siège DEPA** : Bancs d'essai maintenance, HVAC et serveurs informatiques.

---

## ☁️ Architecture Autonome pour Streamlit Community Cloud

L'application a été spécialement conçue pour tourner sans aucune dépendance externe sur Streamlit Community Cloud :

- **Application autonome (`app.py`)** : Le moteur de télémétrie Modbus TCP/IP (20+ compteurs industriels) est intégré directement au sein de `app.py`.
- **Démarrage unique (`@st.cache_resource`)** : Le moteur de simulation est instancié une seule fois par instance de serveur dans un thread en arrière-plan (`daemon=True`), thread-safe, rafraîchissant les mesures toutes les 3 secondes.
- **Résilience aux disques éphémères** : Les données, cumuls d'énergie ($kWh$) et historiques sont gérés en mémoire vive (`in-memory`) avec écriture tolérante dans le dossier relatif `data/`. Aucun risque de plantage si le stockage disque est temporaire ou réinitialisé.
- **Zéro processus externe** : Aucun script `run_all.py`, démon ou tunnel externe n'est requis. Un simple `streamlit run app.py` démarre l'ensemble.

---

## 🚀 Guide de Déploiement sur Streamlit Community Cloud (Gratuit)

### Étape 1 : Initialiser le dépôt Git local

Dans le dossier du projet :
```bash
git init
git add .
git commit -m "Initial commit - SME Marsa Maroc DEPA ISO 50001"
```

### Étape 2 : Créer un dépôt sur GitHub et pousser le code

1. Créez un nouveau dépôt sur [GitHub](https://github.com/new) (par exemple `sme-marsa-maroc`, public ou privé).
2. Liez et poussez votre dépôt local :
```bash
git branch -M main
git remote add origin https://github.com/<VOTRE_UTILISATEUR>/sme-marsa-maroc.git
git push -u origin main
```

### Étape 3 : Déployer sur Streamlit Community Cloud

1. Rendez-vous sur [share.streamlit.io](https://share.streamlit.io) et connectez-vous avec votre compte GitHub.
2. Cliquez sur le bouton **« New app »** (ou « Create app »).
3. Renseignez les paramètres suivants :
   - **Repository :** `<VOTRE_UTILISATEUR>/sme-marsa-maroc`
   - **Branch :** `main`
   - **Main file path :** `app.py`
   - **App URL (optionnel) :** choisissez un sous-domaine personnalisé (ex: `sme-marsa-maroc.streamlit.app`).
4. Cliquez sur **« Deploy! »**.

Streamlit Cloud installe automatiquement les dépendances de `requirements.txt` et votre interface HTTPS permanente est en ligne en moins d'une minute !

---

## 📂 Liste Exacte des Fichiers à Envoyer sur GitHub

Le dépôt est épuré et ne contient que les fichiers nécessaires :

```text
sme-marsa-maroc/
├── .gitignore               # Exclut les binaires, logs, caches et fichiers temporaires
├── .streamlit/
│   └── config.toml          # Thème sombre industriel et configuration serveur Streamlit
├── app.py                   # Application principale autonome avec moteur de simulation intégré
├── index.html               # Synoptique interactif haute fidélité (intégré dans l'onglet 7)
├── modbus_simulator.py      # Simulateur autonome alternatif (CLI ou tests unitaires)
├── requirements.txt         # Dépendances Python compatibles (streamlit, pandas, requests)
└── README.md                # Guide complet du projet et étapes de déploiement
```

---

## 💻 Test en Local (Optionnel)

Pour tester l'application sur votre poste avant le push GitHub :

```bash
pip install -r requirements.txt
streamlit run app.py
```

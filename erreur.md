# 📋 Rapport d'Audit & Liste des Erreurs — Kéranos

Ce document répertorie l'ensemble des erreurs, anomalies, incohérences et risques techniques identifiés dans le projet **Kéranos** lors de l'audit de code.

---

## 🔴 1. Erreurs Bloquantes & Incohérences de Lancement

### 1.1 Références obsolètes au fichier principal (`jarvis14.py` vs `keranos.py`)
- **Fichiers concernés** :
  - `README.md` (ligne 118)
  - `README.en.md` (ligne 91)
  - `INSTALL_WITH_AI.md` (ligne 47)
  - `INSTALL_WITH_AI.en.md` (ligne 45)
  - `scripts/doctor.py` (ligne 268)
  - `scripts/setup.py` (ligne 240)
  - `keranos.py` (ligne 10)
  - `docs/latency.md` (lignes 33, 71)
  - `core/voix.py` (ligne 3)
  - `tools/lumieres.py` (ligne 5)
- **Description** : Le fichier d'entrée a été renommé `keranos.py`, mais les guides, scripts d'installation et diagnostics demandent toujours à l'utilisateur de lancer `uv run python jarvis14.py`.
- **Impact** : Échec immédiat avec `FileNotFoundError: No such file or directory: jarvis14.py`.
- **Correction recommandée** : Remplacer toutes les occurrences de `jarvis14.py` par `keranos.py`.

---

### 1.2 Chemins codés en dur pour `uv.exe` dans les fichiers `.bat`
- **Fichiers concernés** :
  - `lancer_keranos.bat` (ligne 8)
  - `lancer_serveur_mcp.bat` (ligne 9)
- **Description** : Les scripts batch utilisent le chemin en dur `"%USERPROFILE%\.local\bin\uv.exe"`.
- **Impact** : Si `uv` a été installé via `winget`, `pip`, `cargo` ou se trouve dans un autre dossier du `PATH`, le fichier `.bat` échoue avec l'erreur *"Le chemin d'accès spécifié est introuvable"*.
- **Correction recommandée** : Ajouter une vérification dynamique : utiliser `uv` s'il est dans le PATH, et se rabattre sur le chemin local sinon.

---

## 🟠 2. Anomalies Fonctionnelles & Logique Métier

### 2.1 Filtrage excessif des outils en mode local (`_NON_LOCAUX`)
- **Fichier concerné** : `core/registre.py` (lignes 75 à 133)
- **Description** : L'ensemble `_NON_LOCAUX` contient 73 outils, y compris les fonctions domotiques et locales de base :
  - `allumer_lumiere`, `regler_luminosite`, `changer_couleur` (Philips Hue)
  - `activer_mode` (Scènes)
  - `launch_app`, `ajouter_app` (Lancement d'applications PC)
  - `start_record`, `stop_record`, `switch_scene`, `start_stream` (OBS Studio)
  - `controler_gestes`, `ouvrir_panneau`
- **Impact** : En mode local (`mode: local`), `schemas_api(local_seulement=True)` exclut tous ces outils. Le modèle local Ollama est donc incapable d'allumer une lumière ou d'ouvrir une application, rendant le mode local inutile pour le contrôle PC et domotique.
- **Correction recommandée** : Retirer de `_NON_LOCAUX` tous les outils purement locaux (Hue, OBS, Apps, Scènes, Météo locale, Overlay, Gestes) et ne conserver que les outils nécessitant Internet (Gmail, Agenda Google, Twilio, Instagram, Playwright, Hermes).

---

### 2.2 Incohérence du modèle Ollama par défaut
- **Fichiers concernés** :
  - `core/llm.py` (ligne 107) : valeur par défaut `"qwen3.5:4b"`
  - `config.example.yaml` (ligne 13) : valeur par défaut `"qwen2.5:1.5b"`
- **Description** : Divergence entre la valeur de secours dans le code Python et celle documentée dans le fichier YAML.
- **Impact** : Risque d'erreur si l'utilisateur n'a pas configuré de modèle explicite et qu'Ollama ne possède pas le tag `qwen3.5:4b`.
- **Correction recommandée** : Aligner la valeur par défaut sur `qwen2.5:1.5b` (ou `qwen2.5:3b` / `qwen2.5:7b`).

---

## 🟡 3. Qualité de Code & Résidus de Débogage

### 3.1 Condition résiduelle `or True` dans la suspension des crons Hermes
- **Fichier concerné** : `core/routage.py` (ligne 85)
- **Description** :
  ```python
  if _hermes(["cron", "pause", nom], timeout=15) != "" or True:
      suspendus.append(nom)
  ```
- **Impact** : La condition est toujours vraie à cause du `or True`. Le cron est systématiquement considéré comme suspendu, même en cas d'erreur de la commande `hermes`.
- **Correction recommandée** : Supprimer `or True` pour valider correctement la sortie de la commande.

---

## 💡 4. Points d'attention pour l'intégration de Groq

1. **Format des Tool Calls** : L'API Groq suit le standard OpenAI (`/v1/chat/completions`). Il faudra adapter la traduction des schémas d'outils depuis le format Anthropic vers le format JSON Schema d'OpenAI.
2. **Gestion des Rate Limits (HTTP 429)** : Prévoir un mécanisme de repli (fallback) vers Claude ou Ollama si le quota gratuit par minute de Groq est dépassé.
3. **Modèle recommandé** : `llama-3.3-70b-versatile` pour la vitesse et la précision des appels d'outils.

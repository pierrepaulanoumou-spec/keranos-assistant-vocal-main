"""Outils fichiers medias : chercher, lister et ouvrir tes photos/videos/musiques/
documents en local (N1, lecture + ouverture via l'appli par defaut, aucun acces internet)."""
import os
from pathlib import Path

from core.config import reglage
from core.registre import outil

EXTENSIONS = {
    "musique": {".mp3", ".wav", ".flac", ".m4a", ".ogg", ".aac"},
    "video": {".mp4", ".mkv", ".avi", ".mov", ".webm"},
    "photo": {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"},
    "document": {".pdf", ".docx", ".doc", ".txt", ".pptx", ".xlsx"},
}

ALIAS_DOSSIERS = {
    "photos": "Pictures", "images": "Pictures", "photo": "Pictures",
    "videos": "Videos", "video": "Videos",
    "musique": "Music", "musiques": "Music", "audio": "Music",
    "documents": "Documents", "document": "Documents",
    "telechargements": "Downloads", "téléchargements": "Downloads",
}

PROFONDEUR_MAX = int(reglage("fichiers.profondeur_max", 4))


def _dossiers_racine():
    """Dossiers medias par defaut (Images/Videos/Musique/Documents/Telechargements),
    plus d'eventuels dossiers additionnels definis dans config.yaml (fichiers.dossiers)."""
    accueil = Path.home()
    racines = [
        accueil / "Pictures",
        accueil / "Videos",
        accueil / "Music",
        accueil / "Documents",
        accueil / "Downloads",
    ]
    extra = reglage("fichiers.dossiers", []) or []
    racines += [Path(d) for d in extra]
    return [r for r in racines if r.exists()]


def _toutes_extensions(type_media=None):
    if not type_media:
        s = set()
        for e in EXTENSIONS.values():
            s |= e
        return s
    return EXTENSIONS.get(type_media.lower().strip(), set())


def _marcher(racine, profondeur_max):
    """Parcourt un dossier avec une profondeur limitee (evite de scanner des
    arborescences enormes sur une machine peu puissante)."""
    racine_profondeur = str(racine).count(os.sep)
    for courant, sous_dossiers, fichiers in os.walk(racine):
        profondeur = str(courant).count(os.sep) - racine_profondeur
        if profondeur >= profondeur_max:
            sous_dossiers[:] = []
        for nom in fichiers:
            yield Path(courant) / nom


def _recherche(mot_cle, type_media=None, limite=10):
    mot_cle = (mot_cle or "").lower().strip()
    exts = _toutes_extensions(type_media)
    resultats = []
    for racine in _dossiers_racine():
        try:
            for chemin in _marcher(racine, PROFONDEUR_MAX):
                if exts and chemin.suffix.lower() not in exts:
                    continue
                if mot_cle and mot_cle not in chemin.stem.lower():
                    continue
                resultats.append(chemin)
                if len(resultats) >= limite:
                    return resultats
        except Exception:
            continue
    return resultats


@outil(
    nom="chercher_fichiers",
    mcp_expose=True,
    description="Cherche des fichiers medias (photos, videos, musique, documents) sur "
                "l'ordinateur par mot-cle, dans les dossiers personnels (Images, Videos, "
                "Musique, Documents, Telechargements). Utilise pour 'trouve mes photos de...', "
                "'cherche la video...', 'ai-je un fichier...'.",
    parametres={
        "type": "object",
        "properties": {
            "mot_cle": {
                "type": "string",
                "description": "Mot ou partie du nom de fichier a chercher",
            },
            "type_media": {
                "type": "string",
                "enum": ["musique", "video", "photo", "document"],
                "description": "Filtrer par type de fichier (optionnel, tous types si omis)",
            },
        },
        "required": ["mot_cle"],
    },
)
def chercher_fichiers(mot_cle: str, type_media: str = "") -> str:
    """Cherche des fichiers par mot-cle, optionnellement filtres par type."""
    resultats = _recherche(mot_cle, type_media or None, limite=8)
    if not resultats:
        return f"Je n'ai trouve aucun fichier correspondant a {mot_cle}."
    noms = [c.name for c in resultats]
    if len(noms) == 1:
        return f"J'ai trouve un fichier : {noms[0]}."
    return f"J'ai trouve {len(noms)} fichiers : " + ", ".join(noms) + "."


@outil(
    nom="lister_dossier",
    mcp_expose=True,
    description="Liste le contenu d'un dossier personnel connu : photos, videos, "
                "musique, documents ou telechargements. Utilise pour 'qu'est-ce qu'il y a "
                "dans mes photos', 'liste mes documents'.",
    parametres={
        "type": "object",
        "properties": {
            "dossier": {
                "type": "string",
                "description": "Nom du dossier : photos, videos, musique, documents ou "
                               "telechargements",
            },
        },
        "required": ["dossier"],
    },
)
def lister_dossier(dossier: str) -> str:
    """Liste les fichiers presents directement dans un dossier personnel connu."""
    cle = dossier.lower().strip()
    nom_reel = ALIAS_DOSSIERS.get(cle, dossier)
    chemin = Path.home() / nom_reel
    if not chemin.exists():
        return f"Je ne trouve pas le dossier {dossier}."
    fichiers = sorted(f.name for f in chemin.iterdir() if f.is_file())[:15]
    if not fichiers:
        return f"Le dossier {dossier} est vide."
    suffixe = "..." if len(fichiers) == 15 else "."
    return f"Dans {dossier}, il y a : " + ", ".join(fichiers) + suffixe


@outil(
    nom="ouvrir_fichier",
    description="Cherche un fichier media (photo, video, musique, document) par son nom "
                "ou une partie du nom, et l'ouvre avec l'application par defaut de "
                "Windows. Utilise pour 'ouvre le fichier...', 'lance la video...', "
                "'joue la musique...'.",
    parametres={
        "type": "object",
        "properties": {
            "nom": {
                "type": "string",
                "description": "Nom ou partie du nom du fichier a ouvrir",
            },
        },
        "required": ["nom"],
    },
)
def ouvrir_fichier(nom: str) -> str:
    """Cherche un fichier par nom (partiel) et l'ouvre avec l'application par defaut."""
    resultats = _recherche(nom, None, limite=1)
    if not resultats:
        return f"Je n'ai trouve aucun fichier correspondant a {nom}."
    chemin = resultats[0]
    try:
        os.startfile(str(chemin))
        return f"J'ouvre {chemin.name}."
    except Exception as e:
        return f"Je n'ai pas pu ouvrir {chemin.name} ({e})."

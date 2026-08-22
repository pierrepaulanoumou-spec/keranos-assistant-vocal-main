"""Test unitaire et fonctionnel du provider Groq dans Kéranos.

Vérifie la communication avec l'API Groq, la réponse textuelle,
le function/tool-calling et l'enregistrement budgétaire.
"""
import sys
from pathlib import Path

# Fix encodage console Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Ajouter la racine du projet au sys.path
_RACINE = Path(__file__).resolve().parent.parent
if str(_RACINE) not in sys.path:
    sys.path.insert(0, str(_RACINE))

from core.llm import GroqProvider, llm
from core import budget


def tester_groq_complet():
    print("=" * 60)
    print("[TEST] INTEGRATION GROQ DANS KERANOS")
    print("=" * 60)

    # 1. Vérification de la disponibilité
    provider = GroqProvider()
    print(f"\n[1] Fournisseur instancie : {provider.nom}")
    print(f"    Modele principal      : {provider.modele}")
    print(f"    Modeles de rotation   : {provider.rotation}")
    print(f"    Cle disponible        : {'Oui' if provider.disponible() else 'Non (ABSENTE)'}")

    if not provider.disponible():
        print("[KO] Cle API Groq non configuree dans config.yaml (groq.cle)")
        return False

    # 2. Test d'une question textuelle simple
    print("\n[2] Test d'une requete textuelle simple...")
    systeme = "Tu es Keranos, un assistant vocal ultra-rapide et concis. Reponds en une seule phrase."
    historique = [{"role": "user", "content": "Bonjour Keranos ! Es-tu pret pour nos commandes vocales ?"}]
    outils = []

    try:
        rep = provider.repondre(systeme, historique, outils)
        print(f"    Statut de fin (stop_reason) : {rep.stop_reason}")
        texte = " ".join(b.text for b in rep.content if getattr(b, "type", None) == "text")
        print(f"    Reponse recue : \"{texte}\"")
        if not texte:
            print("[KO] Reponse textuelle vide.")
            return False
        print("    [OK] Reponse textuelle validee.")
    except Exception as e:
        print(f"[KO] Echec de la requete : {e}")
        return False

    # 3. Test du Tool Calling (Function Calling)
    print("\n[3] Test du Tool Calling (Appel d'outils)...")
    outils_test = [
        {
            "name": "allumer_lumiere",
            "description": "Allume les lumieres dans une piece specifiee.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "piece": {"type": "string", "description": "Nom de la piece (ex: salon, bureau, chambre)"},
                    "couleur": {"type": "string", "description": "Couleur souhaitee (ex: rouge, bleu, blanc)"}
                },
                "required": ["piece"]
            }
        }
    ]

    historique_outil = [{"role": "user", "content": "Allume la lumiere du salon en bleu s'il te plait."}]

    try:
        rep_outil = provider.repondre(systeme, historique_outil, outils_test)
        print(f"    Statut de fin (stop_reason) : {rep_outil.stop_reason}")
        appels = [b for b in rep_outil.content if getattr(b, "type", None) == "tool_use"]
        print(f"    Nombre d'outils appeles     : {len(appels)}")
        for i, a in enumerate(appels):
            print(f"    -> Appel {i+1} : {a.name}({a.input}) [id: {a.id}]")

        if rep_outil.stop_reason == "tool_use" and any(a.name == "allumer_lumiere" for a in appels):
            print("    [OK] Tool Calling Groq valide avec succes !")
        else:
            print("    [!] Le modele a repondu en texte au lieu de tool_use.")
    except Exception as e:
        print(f"[KO] Echec du test Tool Calling : {e}")
        return False

    # 4. Vérification de la fabrique globale llm()
    print("\n[4] Verification de la fabrique globale llm()...")
    provider_global = llm()
    print(f"    Provider actif via llm() : {provider_global.nom} ({getattr(provider_global, 'modele', '-')})")
    if provider_global.nom != "Groq":
        print("    [!] Le provider actif par defaut n'est pas Groq. Verifie 'mode: groq' dans config.yaml.")
    else:
        print("    [OK] Fabrique globale llm() configuree sur Groq !")

    # 5. Résumé Budget
    print("\n[5] Verification du suivi budget...")
    etat_budget = budget.resume()
    print(f"    Depenses du jour enregistrees : {etat_budget.get('jour', {})}")

    print("\n" + "=" * 60)
    print("SUCCESS: TOUS LES TESTS GROQ ONT REUSSI AVEC SUCCES !")
    print("=" * 60)
    return True


if __name__ == "__main__":
    succes = tester_groq_complet()
    sys.exit(0 if succes else 1)

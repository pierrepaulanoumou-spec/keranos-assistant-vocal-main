"""Outil de verrouillage du PC (N1, reversible et sans danger : verrouiller
n'expose rien, ca protege au contraire la session)."""
import ctypes

from core.registre import outil


@outil(
    nom="verrouiller_pc",
    description="Verrouille la session Windows (ecran de verrouillage). A utiliser "
                "quand l'utilisateur demande de verrouiller le PC, l'ordinateur, "
                "ou la session ('verrouille le PC', 'verrouille l'ecran', 'je pars').",
)
def verrouiller_pc() -> str:
    """Verrouille immediatement la session Windows en cours."""
    try:
        ctypes.windll.user32.LockWorkStation()
        return "PC verrouille."
    except Exception as e:
        return f"Je n'ai pas pu verrouiller le PC ({e})."

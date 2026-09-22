"""
Génération de l'attestation de congé et mécanisme d'authenticité.

Principe : chaque attestation a un numero_serie (UUID) et un hash_verification calculé par
HMAC-SHA256 (clé serveur ATTESTATION_SECRET_KEY, jamais exposée) sur les données figées de la
demande. Le PDF embarque un QR code pointant vers une page de vérification publique
`{FRONTEND_URL}/verification/{numero_serie}?code={fragment}`, où `fragment` est un extrait du
hash. La vérification publique ne réussit que si le fragment fourni correspond au hash stocké
en base — ça empêche de deviner un numéro de série valide par énumération, sans avoir besoin
d'infrastructure de signature numérique externe. Voir docs/00-etat-des-lieux pour le constat
qu'aucun mécanisme équivalent n'existait dans le projet de référence.
"""

import hashlib
import hmac
import io

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from .models import Attestation

FRAGMENT_LENGTH = 12


def _message_canonique(demande, numero_serie) -> str:
    return "|".join(
        [
            str(numero_serie),
            demande.agent.matricule,
            demande.type_conge.code,
            str(demande.date_debut),
            str(demande.date_fin_validee or demande.date_fin_demandee),
        ]
    )


def _calculer_hash(demande, numero_serie) -> str:
    message = _message_canonique(demande, numero_serie)
    return hmac.new(
        settings.ATTESTATION_SECRET_KEY.encode(), message.encode(), hashlib.sha256
    ).hexdigest()


def code_verification_valide(demande, numero_serie, fragment_fourni: str) -> bool:
    hash_reel = _calculer_hash(demande, numero_serie)
    return hmac.compare_digest(hash_reel[:FRAGMENT_LENGTH], fragment_fourni)


def _generer_qr_code_png(url: str) -> bytes:
    img = qrcode.make(url, box_size=6, border=2)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


def _generer_pdf(demande, numero_serie, hash_verification) -> bytes:
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    largeur, hauteur = A4

    y = hauteur - 30 * mm
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(largeur / 2, y, "RÉPUBLIQUE DE GUINÉE")
    y -= 7 * mm
    c.setFont("Helvetica", 11)
    c.drawCentredString(largeur / 2, y, "Ministère de l'Économie, des Finances et du Budget")
    y -= 14 * mm
    c.setFont("Helvetica-Bold", 13)
    c.drawCentredString(largeur / 2, y, "ATTESTATION DE CONGÉ")

    y -= 20 * mm
    c.setFont("Helvetica", 11)
    agent = demande.agent
    lignes = [
        f"Nom et prénom : {agent.last_name} {agent.first_name}",
        f"Matricule : {agent.matricule}",
        f"Type de congé : {demande.type_conge.libelle}",
        f"Période : du {demande.date_debut.strftime('%d/%m/%Y')} "
        f"au {(demande.date_fin_validee or demande.date_fin_demandee).strftime('%d/%m/%Y')}",
        f"Numéro de série : {numero_serie}",
    ]
    for ligne in lignes:
        c.drawString(25 * mm, y, ligne)
        y -= 8 * mm

    fragment = hash_verification[:FRAGMENT_LENGTH]
    url_verification = f"{settings.FRONTEND_URL}/verification/{numero_serie}?code={fragment}"
    qr_png = _generer_qr_code_png(url_verification)
    from reportlab.lib.utils import ImageReader

    c.drawImage(ImageReader(io.BytesIO(qr_png)), 25 * mm, y - 45 * mm, width=35 * mm, height=35 * mm)
    c.setFont("Helvetica-Oblique", 8)
    c.drawString(65 * mm, y - 20 * mm, "Scanner ce QR code pour vérifier l'authenticité de ce document,")
    c.drawString(65 * mm, y - 25 * mm, f"ou consulter : {url_verification}")

    c.showPage()
    c.save()
    return buffer.getvalue()


def generer_attestation(demande) -> Attestation:
    """Crée et enregistre l'Attestation pour une demande approuvée. Idempotent par demande."""
    attestation = Attestation(demande=demande)
    numero_serie = attestation.numero_serie  # généré par le default du modèle (uuid4)
    hash_verification = _calculer_hash(demande, numero_serie)
    pdf_bytes = _generer_pdf(demande, numero_serie, hash_verification)

    attestation.hash_verification = hash_verification
    attestation.fichier_pdf.save(f"attestation-{numero_serie}.pdf", ContentFile(pdf_bytes), save=False)
    attestation.save()
    return attestation

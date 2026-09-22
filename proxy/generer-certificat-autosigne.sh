#!/bin/sh
# Génère un certificat auto-signé pour tester la stack HTTPS en local/démonstration.
# Ne remplace PAS un vrai certificat (Let's Encrypt, etc.) : le navigateur affichera un
# avertissement "connexion non sécurisée", normal pour un certificat auto-signé. En production
# réelle, remplacez proxy/certs/fullchain.pem et privkey.pem par de vrais certificats (ex. via
# certbot avec le challenge DNS ou HTTP-01) pour le nom de domaine réel utilisé.

set -e
cd "$(dirname "$0")/certs"

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout privkey.pem \
  -out fullchain.pem \
  -subj "/C=GN/O=Ministere de l'Economie des Finances et du Budget/CN=localhost"

echo "Certificat auto-signé généré dans proxy/certs/ (valable 365 jours)."

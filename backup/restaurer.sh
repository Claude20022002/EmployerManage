#!/bin/sh
# Restaure une sauvegarde produite par sauvegarder.sh. À lancer manuellement (jamais automatique) :
#   docker compose -f docker-compose.prod.yml --env-file backend/.env run --rm backup \
#     sh /scripts/restaurer.sh employermanage-20260922-030000.sql.gz
#
# ATTENTION : écrase le contenu actuel de la base $POSTGRES_DB. Confirmer avant de lancer.
set -e

if [ -z "$1" ]; then
  echo "Usage : restaurer.sh <nom-du-fichier.sql.gz>  (voir /backups pour la liste disponible)" >&2
  exit 1
fi

fichier="/backups/$1"
if [ ! -f "$fichier" ]; then
  echo "Fichier introuvable : $fichier" >&2
  exit 1
fi

echo "Restauration de $fichier vers la base $POSTGRES_DB sur $POSTGRES_HOST..."
gunzip -c "$fichier" | PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB"
echo "Restauration terminée."

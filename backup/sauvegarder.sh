#!/bin/sh
# Sauvegarde PostgreSQL — boucle infinie : dump toutes les BACKUP_INTERVAL_HEURES heures,
# purge les sauvegardes de plus de BACKUP_RETENTION_JOURS jours. Voir le service `backup` dans
# docker-compose.prod.yml. Les fichiers restent sur le volume `backup-data` (stockage local) :
# pour une vraie résilience (perte de la machine hôte), copier ce volume vers un stockage distant
# (S3, autre serveur...) — non automatisé ici, aucun fournisseur choisi (voir docs/07).
set -e

INTERVALLE_SEC=$(( ${BACKUP_INTERVAL_HEURES:-24} * 3600 ))
RETENTION_JOURS=${BACKUP_RETENTION_JOURS:-14}

echo "Service de sauvegarde démarré : dump toutes les ${BACKUP_INTERVAL_HEURES:-24}h, rétention ${RETENTION_JOURS} jours."

while true; do
  horodatage=$(date +%Y%m%d-%H%M%S)
  fichier="/backups/employermanage-${horodatage}.sql.gz"

  echo "[$(date -Iseconds)] Sauvegarde vers ${fichier}"
  # --clean --if-exists : le dump inclut les DROP nécessaires pour pouvoir être restauré tel
  # quel sur une base déjà peuplée (restauration testée manuellement — voir docs/06, ça échouait
  # sans ces options).
  if PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$POSTGRES_HOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists | gzip > "$fichier"; then
    echo "[$(date -Iseconds)] Sauvegarde réussie ($(du -h "$fichier" | cut -f1))"
  else
    echo "[$(date -Iseconds)] ÉCHEC de la sauvegarde" >&2
  fi

  find /backups -name "employermanage-*.sql.gz" -mtime "+${RETENTION_JOURS}" -delete

  sleep "$INTERVALLE_SEC"
done

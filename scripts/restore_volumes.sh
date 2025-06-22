#!/bin/bash

# Usage: ./scripts/restore_volumes.sh [local|s3] [backup_date_folder]
MODE=${1:-local}
BACKUP_DATE=${2}
BACKUP_DIR="./backups/$BACKUP_DATE"

if [ -z "$BACKUP_DATE" ]; then
  echo "Usage: $0 [local|s3] [backup_date_folder]"
  exit 1
fi

if [ "$MODE" = "s3" ]; then
  # Requires AWS CLI and credentials configured
  S3_BUCKET="s3://your-s3-bucket/agentic-backups/$BACKUP_DATE"
  mkdir -p "$BACKUP_DIR"
  aws s3 cp $S3_BUCKET $BACKUP_DIR --recursive
fi

# List your named volumes here
VOLUMES=("pgdata" "redisdata" "qdrant_data")

for VOLUME in "${VOLUMES[@]}"; do
  ARCHIVE="$BACKUP_DIR/${VOLUME}.tar.gz"
  if [ -f "$ARCHIVE" ]; then
    echo "Restoring $VOLUME from $ARCHIVE"
    docker run --rm -v ${VOLUME}:/volume -v $BACKUP_DIR:/backup alpine \
      sh -c "rm -rf /volume/* && tar xzf /backup/${VOLUME}.tar.gz -C /volume"
  else
    echo "Backup archive $ARCHIVE not found, skipping $VOLUME"
  fi
done

echo "Restore complete from $BACKUP_DIR"
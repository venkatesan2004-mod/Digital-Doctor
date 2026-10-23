# Digital Doctor: Database Backup & Disaster Recovery Procedures

## 1. Relational Database Backup (MySQL 8.0)

### 1.1 Automated Logical Backup (mysqldump)
Run the backup command targeting the containerized MySQL service:
```bash
docker compose exec mysql mysqldump -u digital_doctor_app -pdev_secret_doctor_pw_2026 \
  --single-transaction --quick --routines --triggers digital_doctor > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 1.2 Database Restoration
To restore a snapshot into a clean MySQL database instance:
```bash
docker compose exec -T mysql mysql -u digital_doctor_app -pdev_secret_doctor_pw_2026 digital_doctor < backup_20261023_120000.sql
```

---

## 2. ChromaDB Vector Store Backup

ChromaDB state is persisted in the Docker named volume `digital_doctor_chroma_data` under `/chroma/chroma`.

### Volume Snapshot Procedure:
```bash
docker run --rm -v digital_doctor_chroma_data:/data -v $(pwd)/backups:/backup \
  alpine tar czf /backup/chroma_backup_$(date +%Y%m%d).tar.gz -C /data .
```

### Volume Restoration:
```bash
docker run --rm -v digital_doctor_chroma_data:/data -v $(pwd)/backups:/backup \
  alpine tar xzf /backup/chroma_backup_20261023.tar.gz -C /data
```

---

## 3. Uploaded Medical Documents Backup

Uploaded reports and scans reside in the named volume `digital_doctor_uploads`:
```bash
docker run --rm -v digital_doctor_uploads:/uploads -v $(pwd)/backups:/backup \
  alpine tar czf /backup/uploads_backup_$(date +%Y%m%d).tar.gz -C /uploads .
```

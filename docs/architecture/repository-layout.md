# Repository Layout

## Root Directory

| Path | Purpose |
|---|---|
| pocket.py | Main runtime engine |
| docker-compose.yml | Service orchestration |
| requirements.txt | Python dependency snapshot |
| pocket-identity.md | Canonical identity document |

---

## Major Directories

### chroma_data/
Persistent ChromaDB vector memory storage.

DO NOT:
- Edit manually
- Delete without backup

---

### app/
Electron avatar application.

Contains:
- Window logic
- Avatar rendering
- WebSocket communication

---

### docs/
Project documentation and engineering records.

---

### pocket_backups/
Automatic rollback and recovery backups.

---

## Planned Future Structure

```text
memory/
voice/
avatar/
executor/
tools/
vision/
integrations/
```
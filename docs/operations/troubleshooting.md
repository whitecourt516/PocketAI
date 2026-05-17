# Troubleshooting Guide

# Purpose

This document contains operational troubleshooting procedures for Pocket.

Goals:
- Diagnose runtime failures
- Recover broken services
- Verify system integrity
- Standardize debugging workflow
- Preserve operational knowledge

This document is intended for:
- Human debugging
- Future AI-assisted troubleshooting
- Recovery documentation
- Development continuity

---

# General Diagnostic Workflow

When Pocket experiences problems:

1. Identify affected subsystem
2. Verify service availability
3. Check logs/output
4. Confirm dependency health
5. Attempt subsystem restart
6. Escalate to recovery procedures if needed

---

# Startup Failures

## Ollama Not Responding

### Symptoms
- Pocket hangs while generating
- No response returned
- Connection errors
- Model requests timeout

### Checks

```bash
ollama list
```

```bash
docker ps
```

Verify:
- Ollama service is running
- Model exists
- GPU resources available

### Fixes
- Restart Ollama
- Restart Docker containers
- Verify GPU availability
- Re-pull damaged model if necessary

---

## Docker Container Failure

### Symptoms
- Services unavailable
- ChromaDB inaccessible
- Startup failures

### Checks

```bash
docker ps
```

```bash
docker compose logs
```

### Fixes
- Restart containers
- Verify mounted volumes
- Check port conflicts
- Rebuild containers if corrupted

---

# Memory System Issues

## ChromaDB Issues

### Symptoms
- Memory retrieval empty
- Errors during storage
- Persistence failure
- Missing contextual memory

### Checks

Verify:

```text
chroma_data/
```

exists and is mounted correctly.

Verify:
- Database files exist
- Disk space available
- Containers mounted properly

### Fixes
- Restart containers
- Restore from backup if corrupted
- Rebuild memory collection if necessary

### Escalation
If corruption persists:
1. Stop services
2. Restore latest stable backup
3. Verify retrieval functionality
4. Re-index memory if needed

---

# Voice System Issues

## Whisper Failure

### Symptoms
- No transcription
- Delayed recognition
- Incorrect speech parsing

### Checks
- Verify microphone permissions
- Verify Whisper model loaded
- Test microphone input independently

### Fixes
- Restart transcription service
- Reload model
- Reconnect audio devices

---

## Piper TTS Failure

### Symptoms
- Text output works
- No speech audio
- Distorted speech
- Delayed playback

### Checks
- Verify Piper executable
- Check output device
- Verify voice model exists
- Confirm audio routing

### Fixes
- Restart audio services
- Reload Piper model
- Reconnect audio devices

---

# Avatar System Issues

## Electron Avatar Not Appearing

### Symptoms
- No avatar window
- Frozen frontend
- Blank Electron application

### Checks
- WebSocket port available
- Electron app launched
- No hidden window state
- Node modules installed

### Commands

```bash
npm install
```

```bash
npm start
```

### Fixes
- Restart Electron app
- Reinstall node modules
- Verify frontend/backend communication

---
## Import / Module Errors

### Symptoms
- `ModuleNotFoundError` on startup
- `ImportError` for core.* modules
- Pocket starts but subsystems silent

### Checks
- Verify file exists at expected path (core/tts.py, core/stt.py, etc.)
- Verify you're running from project root: `cd C:\Users\white\PocketAI`
- Check `__pycache__` isn't stale — delete and rerun

### Fixes
- Confirm all core/ and config/ files are present
- Re-run from correct directory
- Run smoke test to isolate which module is broken:
  `python tests/smoke_test.py`


---

## Expression Engine Failure

### Symptoms
- Avatar not reacting
- Incorrect emotional states
- Animation desynchronization

### Checks
- Verify WebSocket connection
- Verify expression mapping logic
- Confirm backend emotion state output

### Fixes
- Restart frontend
- Reset expression state
- Simplify conflicting animation logic

---

# Repository / Git Issues

## Git Ignore Problems

### Symptoms
- Runtime data tracked accidentally
- Large files pushed to repository
- Repository size growth

### Checks

```bash
git status
```

```bash
git ls-files
```

### Fixes
- Update `.gitignore`
- Remove cached tracking:

```bash
git rm -r --cached <path>
```

---

# Emergency Recovery

## Restore From Backup

### Procedure

1. Stop all services
2. Backup current broken state
3. Restore latest stable backup
4. Restart services
5. Verify:
   - memory retrieval
   - voice systems
   - avatar systems
   - frontend communication

---

# Verification Checklist

After major fixes verify:

- Ollama responding
- ChromaDB mounted
- Voice input functioning
- TTS output functioning
- Avatar responding
- WebSocket connected
- Memory retrieval functioning
- No critical console errors
- Smoke test passing: 'python tests/smoke_test.py'

---

# Future Expansion Areas

Planned future troubleshooting coverage:
- autonomous systems
- tool execution
- memory pruning
- multi-agent coordination
- procedural animation
- environment interaction systems
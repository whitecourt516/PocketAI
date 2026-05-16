\# Troubleshooting Guide



\## Ollama Not Responding



\### Symptoms

\- Pocket hangs while generating

\- No response returned

\- Connection errors



\### Checks

```bash

ollama list

```



```bash

docker ps

```



\### Fixes

\- Restart Ollama

\- Restart Docker containers

\- Verify GPU availability



\---



\## ChromaDB Issues



\### Symptoms

\- Memory retrieval empty

\- Errors during storage

\- Persistence failure



\### Checks

Verify:

```text

chroma\_data/

```

exists and is mounted correctly.



\### Fixes

\- Restart containers

\- Restore from backup if corrupted



\---



\## Electron Avatar Not Appearing



\### Checks

\- WebSocket port available

\- Electron app launched

\- No hidden window state



\---



\## Piper TTS Failure



\### Symptoms

\- Text output works

\- No speech audio



\### Fixes

\- Verify Piper executable

\- Check output device

\- Restart audio services


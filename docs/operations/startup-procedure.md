\# Startup Procedure



\## Standard Startup Sequence



\### 1. Start Docker Services

```bash

docker compose up -d

```



\---



\### 2. Verify Containers

```bash

docker ps

```



\---



\### 3. Verify Ollama

```bash

ollama list

```



\---



\### 4. Launch Pocket Core

```bash

python pocket.py

```



\---



\### 5. Launch Electron Avatar

```bash

cd app

npm start

```



\---



\## Verification Checklist



\- Ollama responding

\- ChromaDB mounted

\- Voice input functioning

\- TTS output functioning

\- Avatar responding

\- WebSocket connected


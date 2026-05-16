\# Pocket System Overview



\## Project Purpose



Pocket is a local-first AI companion system focused on:

\- conversational interaction,

\- persistent memory,

\- emotional expression,

\- visual embodiment,

\- and long-term extensible autonomy.



\---



\# High-Level System Architecture



User

↓

Voice Input

↓

Speech-to-Text (Whisper)

↓

Pocket Core Processing

↓

Memory Retrieval (ChromaDB)

↓

LLM Processing (Ollama)

↓

Response Generation

↓

Expression Engine

↓

Text-to-Speech (Piper)

↓

Electron Avatar Interface

↓

User Output



\---



\# Core Systems



\## 1. Pocket Core

Primary orchestration layer.



Responsibilities:

\- Conversation handling

\- Context management

\- Memory coordination

\- Response generation

\- System routing



Primary file:

```text

pocket.py

```



\---



\## 2. Memory System

Persistent semantic memory using vector storage.



Technologies:

\- ChromaDB

\- Embedding generation

\- Retrieval-augmented prompting



Persistent storage:

```text

chroma\_data/

```



\---



\## 3. Voice System

Handles:

\- speech input

\- speech transcription

\- spoken output



Components:

\- Whisper

\- Piper



\---



\## 4. Avatar System

Visual frontend and emotional expression layer.



Components:

\- Electron

\- WebSockets

\- Expression engine

\- Frontend renderer



Directory:

```text

app/

```



\---



\# Communication Flow



\## User Input Flow



User Speech

↓

Whisper

↓

Pocket Core

↓

Memory Retrieval

↓

LLM Processing



\---



\## Output Flow



LLM Response

↓

Expression State Assignment

↓

Piper TTS

↓

Electron Avatar Update

↓

User Output



\---



\# Data Persistence



\## Persisted Data

\- Vector memory database

\- Configuration files

\- Documentation

\- Logs

\- Git history



\## Non-Persisted Runtime Data

\- Temporary audio

\- Cached inference artifacts

\- Session-only states



\---



\# Repository Layout



\## Important Directories



| Directory | Purpose |

|---|---|

| docs/ | Documentation |

| app/ | Electron frontend |

| chroma\_data/ | Persistent vector database |

| pocket\_backups/ | Recovery snapshots |

| piper/ | Local TTS assets |



\---



\# Current Architectural Priorities



Current development focus:

\- emotional systems

\- avatar responsiveness

\- system cohesion

\- memory quality

\- infrastructure stability



\---



\# Long-Term Architectural Direction



Planned future expansion:

\- autonomous behaviors

\- modular tool systems

\- advanced memory layers

\- procedural animation

\- environmental awareness

\- multi-agent orchestration



\---



\# Development Philosophy



Pocket prioritizes:

\- local-first operation

\- modular architecture

\- extensibility

\- recoverability

\- maintainability

\- personality-driven interaction


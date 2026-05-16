\# Decision — ChromaDB Memory System



Date: 2026-05-13



\---



\## Decision

Pocket will use ChromaDB as its primary persistent conversational memory layer.



\---



\## Reasoning



Requirements:

\- Fully local

\- Persistent across sessions

\- Semantic retrieval

\- Lightweight setup

\- Easy Python integration



ChromaDB satisfied all requirements while remaining simple enough for early-stage development.



\---



\## Alternatives Considered



\### SQLite

Pros:

\- Simple

\- Stable



Cons:

\- No semantic retrieval

\- Manual search complexity



\---



\### Fine-Tuning

Pros:

\- Deep behavioral learning



Cons:

\- Slow iteration

\- Expensive retraining

\- Harder debugging



\---



\## Tradeoffs Accepted



\- More infrastructure complexity

\- Vector debugging is harder

\- Retrieval quality requires tuning



\---



\## Future Implications



Future systems depending on this:

\- Reflection systems

\- Memory Vault

\- Semantic Search

\- Knowledge Graph



Future concerns:

\- Memory pruning

\- Retrieval quality degradation

\- Metadata expansion


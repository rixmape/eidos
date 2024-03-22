# Eidos

Eidos is a web app designed to facilitate learning in philosophy through AI-driven Socratic dialogue. The ambition is to make the study of philosophy more accessible, interactive, and reflective. This app utilizes technologies such as a large language model for generating responses, a vector database of publicly-available philosophy texts for reference, and customization features for a personalized user experience.

```mermaid
---
title: AI-Driven Socratic Dialogue

---
flowchart TD
    A[Eidos suggests some definitions to explore] --> B[User chooses a definition or proposes a new one]
    B --> C{Check prompt limit}
    C -- Within Limit --> D[Fetch relevant documents for reference]
    D --> E{Inconsistent definition?}
    E -- Yes --> F[Point out inconsistency
    and ask for clarification]
    F --> G[User refines definition or
    provides some examples]
    G --> C
    E -- No --> H[Explore deeper implications
    and ask for examples]
    H --> G
    C -- Limit Reached --> I[Show reply to last prompt]
    I --> J[Summarize dialogue]
    J --> K[Recommend further reading]
    K --> Z[End dialogue]
```

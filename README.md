# Eidos

Eidos is a web app designed to facilitate learning in philosophy through AI-driven Socratic dialogue. The ambition is to make the study of philosophy more accessible, interactive, and reflective. This app utilizes technologies such as a large language model for generating responses, a vector database of publicly-available philosophy texts for reference, and customization features for a personalized user experience.

```mermaid
flowchart TD
    A[Eidos suggests some definitions to explore] --> B[User chooses a definition or proposes a new one] --> C{Check prompt limit}
    C -- Within Limit --> D[Fetch relevant documents for reference] --> E{Inconsistent definition?}
    E -- Yes --> F[Point out inconsistency and ask for clarification]
    F --> G[User refines or re-proposes definition] --> C
    E -- No --> H[Explore deeper implications and ask question] --> G
    C -- Limit Reached --> I[Show reply to last prompt and end dialog]
```

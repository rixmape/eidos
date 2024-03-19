# Eidos

Eidos is a web app designed to facilitate learning in philosophy through AI-driven Socratic dialogue. Its objective is to make philosophical education more interactive and personalized, encouraging deep understanding and critical thinking. The app utilizes technologies such as a large language model for generating dialogue, a vector database for course materials, and user customization features for a tailored learning experience.

```mermaid
sequenceDiagram
    title: Step-by-Step Process

    autonumber
    participant User
    participant App
    participant DocumentManager as Document Manager
    participant Model as Language Model

    note over DocumentManager: Conatins course materials

    User->>App: Send Message
    App->>DocumentManager: Send User Message
    DocumentManager-->>App: Relevant Documents
    App->>Model: Send User Message and Documents
    Model-->>App: Response
    App-->>User: Display Response
```

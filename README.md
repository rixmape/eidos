# Just Another Chatbot

This project is a chatbot application built with Python and Streamlit. It uses the OpenAI language model to generate responses to user queries.

## Features

- Customizable chatbot settings: You can configure the chatbot's language style, dialogue pace, and topic.
- Document upload: You can upload text documents that the chatbot will use to generate responses.
- Interactive chat interface: You can interact with the chatbot in a chat-like interface.

## Installation

1. Clone this repository.
2. Install the required Python packages:

```sh
pip install -r requirements.txt
```

3. Configure the `.streamlit/secrets.toml` file with your OpenAI API key:

```toml
[env]
OPENAI_API_KEY = ""
LANGCHAIN_TRACING_V2 = ""
LANGCHAIN_ENDPOINT = ""
LANGCHAIN_API_KEY = ""
LANGCHAIN_PROJECT = ""

[params]
model = ""

[messages]
system = "You are a helpful assistant. You can help me with my questions."
initial = "Hello! Can you tell me something you know?"

[topics]
physics = "You are an expert in physics."
mathematics = "You are an expert in mathematics."
history = "You are an expert in history."

[language_styles]
formal = "Always use formal language."
casual = "Use casual language."

[dialogue_paces]
in-depth = "Take your time to respond."
quick = "Respond quickly."
```

## Usage

1. Run the main script:

    ```sh
    python main.py
    ```

2. Open your web browser and navigate to the local server address displayed in your terminal.

## License

This project is licensed under the MIT License. See the [`LICENSE`](LICENSE) file for more details.

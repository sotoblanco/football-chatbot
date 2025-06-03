
## Core components

- Backend (FastAPI): Serves the frontend and provides an API endpoint (/chat) for the chatbot logic.
- Frontend (HTML/CSS/JS): A basic, modern chat interface where users can send messages and receive responses.
    - Renders assistant responses as Markdown.
    - Includes a typing indicator for better user experience.
- LLM Integration (LiteLLM): The backend connects to an LLM (configurable via .env) to generate scouting advice.

## Project structure

```
football-chatbot/
├── backend/
│   ├── __init__.py
│   ├── main.py         # FastAPI application, routes
│   └── utils.py        # LiteLLM wrapper, system prompt, env loading
├── data/
├── frontend/
│   └── index.html      # Chat UI (HTML, CSS, JavaScript)
├── .env.example        # Example environment file
├── requirements.txt    # Python dependencies
└── README.md           # This file (Your guide!)
```

## Setup Instructions

1.  **Clone the Repository (if you haven't already)**
    ```bash
    git clone https://github.com/sotoblanco/football-chatbot.git
    cd football-chatbot
    ```

2.  **Create and Activate a Python Virtual Environment**
    ```bash
    python -m venv .venv
    ```
    *   On macOS/Linux:
        ```bash
        source .venv/bin/activate
        ```
    *   On Windows:
        ```bash
        .venv\Scripts\activate
        ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables (`.env` file)**
    *   Copy the example environment file:
        ```bash
        cp env.example .env
        ```
        (or `cp .env.example .env` if you have that one)
    *   Edit the `.env` file. You will need to:
        1.  Set the `MODEL_NAME` to the specific model you want to use (e.g., `openai/gpt-4.1-nano`, `anthropic/claude-3-opus-20240229`, `ollama/llama2`).
        2.  Set the **appropriate API key environment variable** for the chosen model provider. 
            Refer to your `env.example` for common API key names like `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GEMINI_API_KEY`, etc. 
            LiteLLM will automatically use these provider-specific keys.

        Example of a configured `.env` file if using an OpenAI model:
        ```env
        MODEL_NAME=openai/gpt-4.1-nano
        OPENAI_API_KEY=sk-yourActualOpenAIKey...
        ```
        Example for an Anthropic model:
        ```env
        MODEL_NAME=anthropic/claude-3-haiku-20240307
        ANTHROPIC_API_KEY=sk-ant-yourActualAnthropicKey...
        ```

    *   **Important - Model Naming and API Keys with LiteLLM**:
        LiteLLM supports a wide array of model providers. To use a model from a specific provider, you generally need to:
        *   **Prefix the `MODEL_NAME`** correctly (e.g., `openai/`, `anthropic/`, `mistral/`, `ollama/`).
        *   **Set the corresponding API key variable** in your `.env` file (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `MISTRAL_API_KEY`). Some local models like Ollama might not require an API key.

        Please refer to the official LiteLLM documentation for the correct model prefixes and required environment variables for your chosen provider: [LiteLLM Supported Providers](https://docs.litellm.ai/docs/providers).

## Running the Provided Application

### 1. Run the Web Application (Frontend and Backend)

*   Ensure your virtual environment is activated and your `.env` file is configured.
*   From the project root directory, start the FastAPI server using Uvicorn:
    ```bash
    uvicorn backend.main:app --reload
    ```
*   Open your web browser and navigate to: `http://127.0.0.1:8000`

    You should see the chat interface.



## Evals

This project is made in the context of the AI Evals by Shreya and Hamel

As our first step we build the bridge between the Developer and the LLM Pipeline by creating a specific prompt that follows:

1. Role
2. Instruction
3. Context
4. Examples
5. Reasoning for complex problems
6. Output format
7. Delimeters and structure

We then follow the Error analysis process that consists in three step:

1. Analyze
2. Measure
3. Improve

## Analyze

This consists in five steps that helps to analyze our failure modes

1. Boostrap initial dataset

We need to generated queries that are likely to fail, you might wonder how can I know if something will fail: test your application! The best way to understand and extract some failure modes is by using your application yourself.

The goal is to have 100 traces, and being diverse enought to are likely to get a failure mode, remember we need to find failures in our application. Since we might not have users at first we can create syntetic data, but this needs to be target to identify failure modes.

### Dimensions

- Country requirements
- Price requirements
- Player comparison
- Target position
- Ambiguous query



In our football dataset this are potential failure modes

![alt text](images/image.png)

This is a failure mode, in reality there is no football player who names is Cristian Rivas from venezuela under 19 years old and goal keeper.

![alt text](images/image2.png)

The players from that club do not have this player.

THere are more than one failure mode here:

- I didn't ask for a goal keeper
- The dataset might be capped to the model train, but still that player doesn't exists with those characteristics
- Age constraits might be difficult to get without real-time data
- Some countries and clubs might be difficult to get data as the model is likely to not be as expose as other data

![alt text](images/image3.png)

This confirms that the data is cut-off to 2023, so base on our own use case we might add a tool to get updated data, we won't write an eval for this as it can be fix with a tool calling mecahnism.

### Tuples

Combination of dimension gives tuples that creates queries that are more likely to triger errors in our application

Example:

| Find a player that is similar to Messi, from Grece and plays as winger

This query combines three dimensions:
- Country
- Player skills
- Scenario

As expected it trigger a failure mode:

![alt text](images/image4.png)

Although it provide a disclaimer that he is not messi it missed the club, dimitrio has never played at olympiacos as our chat bot said

![alt text](images/image5.png)

Generate the tupples with LLMs
- Country requirements
- Player skills
- Ambiguous query


**Sample prompt for tupple combination**

> Generate 10 random combinations of (country, player skills, scenario) for a football scouting assistant.
> The dimensions are:
> Country: the players nationality. Possible values: Argentina, Brazil, Spain, Venezuela...
> Player skills: specific skills for each player, that includes compare players with other current or past players. Possible values: A player similar to messi, A player with a good awarness, Strong defensive players in off-side systems
> Scenario: how well-formed or challenging the query is.
> Possible values:
> • exact match (clearly specified and feasible),
> • ambiguous request (unclear or underspecified),
> • shouldn't be handled (invalid or out-of-scope).
> 
> Output each tuple in the format: (country, player comparison , ambigous query)
> Avoid duplicates. Vary values across dimensions. The goal is to create a diverse set of queries for our assistant.

This is what I got from Gemini:

```
(Spain, A player with excellent passing range like Xavi, exact match)
(Brazil, Strong defensive players in off-side systems, ambiguous request)
(Argentina, A player similar to Messi, exact match)
(Venezuela, A player with a good awareness, exact match)
(Germany, A player who can be the next Franz Beckenbauer, ambiguous request)
(France, A striker with clinical finishing, exact match)
(Colombia, Players who excel in high-pressing tactics, ambiguous request)
(Portugal, A winger with blistering pace and dribbling, exact match)
(Netherlands, A tall, dominant center-back, exact match)
(Uruguay, Any player who is good, shouldn't be handled)
```



For each LLM-generated tuple, we then generate a full query in natural language. The second prompt might look like:

**Sample prompt for natural language query**

> We are generating synthetic user queries for a football scouting assistant. The assistant helps scouters find players compare strengths and abilities and provide recomendations for new players.
> Given:
> - Country: Portugal
> - Player skills: A player with excellent passing range like Xavi
> - Scenario: exact match
>
> Write a realistic query that an agent might enter into the system to fulfill this client’s request. The query should reflect the client’s needs and the ambiguity of the scenario.
>
> Example:
> “Find a strong player from portugal”
>
> Now generate a new query.

Gemini response:

```
Find a Portuguese midfielder with an exceptional passing range, similar to Xavi.
```
# Bytecrafter CLI 🤖

Welcome to Bytecrafter CLI, a powerful, native AI-powered command-line agent that leverages APIs from a variety of vendors to help you with your coding tasks.

It acts as your personal programming assistant directly in your terminal, allowing you to create, read, and edit files, as well as execute commands.

## ✨ Features

-   **🤖 Gemini-Powered Agent**: Leverages the power and accuracy of Google's `gemini-2.5-flash-lite-preview-06-17` model.
-   **🛠️ Robust Tool-Using**: Uses Gemini's native function calling for reliable and precise tool execution.
-   **📂 File Manipulation**: Can read, create, and edit files within your project.
-   **💻 Command Execution**: Can execute shell commands to build, test, or run your code.
-   **📦 Containerized with Docker**: Easy setup and a consistent runtime environment.
-   **📑 Advanced File Tools**: `replace_in_file`, `search_files`, `list_code_definition_names` with encoding-safe operations 
-   **🧠 Persistent Memory System**: PostgreSQL-backed conversation and project memory, enabling true long-term context (see [memory_system_design.md](memory_system_design.md)).
-   **🖥️ Remote Browser Automation**: Control Chrome/Chromium sessions (start, navigate, screenshot) for end-to-end web testing.
-   **📋 Integrated Task Manager**: Create tasks, start work, break them into subtasks, and track progress directly from the chat.
-   **🔌 MCP Extensibility (Prototype)**: Register and use external Model-Context-Protocol servers over STDIO to add infinite new tools (`mcp_add_server`, `mcp_execute_tool`).
-   **❓ Enhanced Follow-up Questions**: Ask clarification questions with multiple choice options for smoother interactions.
-   **📝 Continuous Improvement**: Dozens of bug fixes, better error messages, and encoding detection. Full list in [NUEVAS_FUNCIONALIDADES.md](NUEVAS_FUNCIONALIDADES.md).

## 📋 Prerequisites

Before you begin, ensure you have the following installed:

-   [Docker](https://docs.docker.com/get-docker/)
-   [Docker Compose](https://docs.docker.com/compose/install/)

## 🚀 Getting Started

Follow these steps to get Bytecrafter CLI up and running.

### 1. Clone the Repository

```bash
git clone [<YOUR_REPOSITORY_URL>](https://github.com/scharss/bytecraftercli.git)
cd bytecraftercli
```

### 2. Get your Gemini API Key

This project requires a Google Gemini API key.

1.  Go to [Google AI Studio](https://aistudio.google.com/app/apikey).
2.  Click **"Create API key"** and copy your new key.

### 3. Create your Environment File (`.env`)

You need to create a `.env` file to store your API key.

-   **On Linux/macOS:**
    ```bash
    cp .env.example .env
    ```
-   **On Windows (PowerShell):**
    ```powershell
    copy .env.example .env
    ```

Now, open the newly created `.env` file and **paste your Gemini API key** into it:

```env
# Get your API key from Google AI Studio: https://aistudio.google.com/app/apikey
GEMINI_API_KEY="AIzaSy...your...key...here..."
```

### 4. Build and Run the Agent

With the `.env` file configured, you can now start the agent.

-   **On Linux/macOS:**
    You can use the helper script `run.sh`. First, make it executable:
    ```bash
    chmod +x run.sh
    ```
    Then, run it:
    ```bash
    ./run.sh
    ```

-   **On Windows (PowerShell):**
    Execute the following commands in order:
    1.  **Build and start the service:**
        ```powershell
        docker-compose up -d --build
        ```
    2.  **Start an interactive session:**
        ```powershell
        docker-compose exec bytecrafter python -m bytecrafter.main
        ```

### 5. Start Interacting!

You are now in an interactive session with the Bytecrafter agent. Start giving it instructions!

```
Welcome to Bytecrafter CLI ! 🤖
Your AI assistant for coding tasks. Type 'exit' or 'quit' to end.
You: >>>
```

When you are finished, type `exit` in the agent's prompt, and then run `docker-compose down` to stop the services.



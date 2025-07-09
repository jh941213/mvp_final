# Installation

## Create a Virtual Environment (optional)

When installing AgentChat locally, we recommend using a virtual environment for the installation. This will ensure that the dependencies for AgentChat are isolated from the rest of your system.

### venv

Create and activate:

**Linux/Mac:**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

**Windows command-line:**

```bash
python3 -m venv .venv
.venv\Scripts\activate.bat
```

To deactivate later, run:

```bash
deactivate
```

### conda

## Install using pip

Install the autogen-core package using pip:

```bash
pip install "autogen-core"
```

> **Note:** Python 3.10 or later is required.

## Install OpenAI for Model Client

To use the OpenAI and Azure OpenAI models, you need to install the following extensions:

```bash
pip install "autogen-ext[openai]"
```

If you are using Azure OpenAI with AAD authentication, you need to install the following:

```bash
pip install "autogen-ext[azure]"
```

## Install Docker for Code Execution (Optional)

We recommend using Docker to use DockerCommandLineCodeExecutor for execution of model-generated code. To install Docker, follow the instructions for your operating system on the Docker website.

To learn more code execution, see Command Line Code Executors and Code Execution.

---

**Navigation:**
- Previous: Core
- Next: Quick Start

**On this page:**
- Create a Virtual Environment (optional)
- Install using pip
- Install OpenAI for Model Client
- Install Docker for Code Execution (Optional)


<p align="center">
  <img src="assets/logo.png" alt="Protokol Logo" width="500"/>
</p>

# Protokol 🚀

**The Ultra-Lightweight, Enterprise-Grade LLM Orchestration Framework for Python.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Enterprise Ready](https://img.shields.io/badge/Enterprise-Ready-success.svg)](#)

**Protokol** is a pure, stateless routing protocol and state machine for building complex AI Agent workflows. Unlike opinionated frameworks (like LangChain or LlamaIndex) that force you into their API wrappers, tool decorators, and networking logic, Protokol strictly handles the **"Brain"** (state management and routing) and leaves the execution entirely to you.

It's the ultimate **Bring Your Own LLM (BYO-LLM)** framework.

---

## 🌟 Why Protokol? (The "Bring Your Own LLM" Paradigm)

Most AI Agent frameworks tightly couple the execution logic with the routing logic. This leads to bloated dependencies, opaque API calls, and rigid schemas that break the moment you need custom infrastructure. 

Protokol flips this on its head using **Inversion of Control**:
1. **No Network Requests:** Protokol has zero HTTP dependencies. It never calls an API.
2. **Zero Tool Schemas:** You simply yield string names of tools (e.g., `["issue_refund"]`). *You* handle the actual execution.
3. **Immutably Traceable:** Every state transition is recorded in an immutable audit log (`plan.trace`), making it perfect for highly regulated industries (Finance, Healthcare).
4. **Resumable (Human-in-the-Loop):** Flows can safely pause, serialize to JSON, and be hydrated weeks later when a human manager approves a step.

### When to Use Protokol ✅
* You are building **enterprise AI systems** (FastAPI, Celery, Kafka) where you need absolute control over API keys, network calls, and retries.
* You need **Human-in-the-loop** interactions that survive server restarts.
* You are building complex, multi-turn AI chatbots that require strict routing paths (e.g., *Customer must provide an Order ID before advancing*).
* You want to use multiple LLM providers (OpenAI for routing, local vLLM for extraction) without dealing with framework abstractions.

### When NOT to Use Protokol ❌
* You want a quick script that magically connects to OpenAI and runs a web search in 3 lines of code. (Use `OpenAI Assistants API` or `LangChain` instead).
* You do not want to write your own HTTP/LLM execution loop.

---

## 🏗️ Core Architecture

Protokol consists of three main concepts:
1. **`AbstractStep`**: A node in the graph. It yields instructions (`StepContext`) and processes the result.
2. **`AbstractFlow`**: A collection of Steps. (Flows can be nested infinitely!).
3. **`RunPlan`**: The serializable memory object tracking the state, retry attempts, and the audit log.

---

## 📦 Installation

Protokol is published on PyPI as [`protokol-core`](https://pypi.org/project/protokol-core/) and targets Python **3.10+**.

```bash
python -m pip install protokol-core
```

Prefer using a virtual environment (e.g., `python -m venv .venv && source .venv/bin/activate`) or a modern tool like [uv](https://github.com/astral-sh/uv):

```bash
uv add protokol-core
```

Once installed, you can import every public building block via `from protokol import ...`.

📚 **Docs:** Full documentation (guides + API reference) now lives at [https://souvik666.github.io/protokol-core/](https://souvik666.github.io/protokol-core/). To build locally run `pip install .[docs] && PYTHONPATH=src mkdocs serve`.

🚢 **Releases:** Every push to `main` that follows Conventional Commits triggers semantic-release, which tags the repo, creates a GitHub release, and uploads the fresh build to [PyPI](https://pypi.org/project/protokol-core/).

---

## ✨ Minimal Example

Need a tiny script to understand the moving pieces? The example below wires a single step into a flow, asks the engine for instructions, and feeds back a mocked LLM response:

```python
from protokol import AbstractFlow, AbstractStep, Engine, RunPlan, StepContext


class CollectGreetingStep(AbstractStep):
    id = "collect_greeting"

    def get_context(self, plan: RunPlan) -> StepContext:
        return StepContext(
            prompt="Ask the user to say hello and return 'GREETING: <text>'",
            tools=[]
        )

    def process(self, plan: RunPlan, user_result: str) -> dict:
        plan.state["greeting"] = user_result.replace("GREETING:", "").strip()
        return {"status": "success"}

    def next(self, plan: RunPlan, output: dict):
        plan.is_terminal = True
        return None


class GreetingFlow(AbstractFlow):
    id = "greeting_flow"
    steps = {"collect_greeting": CollectGreetingStep}


flow = GreetingFlow()
engine = Engine()
plan = RunPlan(current_step="collect_greeting")

context = engine.get_context(flow, plan)
print("Prompt for your executor:", context.prompt)

# Pretend your own execution layer called an LLM and received a response
mock_llm_response = "GREETING: Hi there!"
engine.advance(flow, plan, mock_llm_response)

print("Recorded state:", plan.state)
```

Run it after installing `protokol-core`; the script prints the instruction the engine generated, then shows the state captured once the mocked response is processed.

---

## 🚀 Quickstart: End-to-End Usage

Here is how you build a strict conversational state machine.

### 1. Define Your Steps
Steps dictate *what* needs to happen, but they do not execute it.

```python
from core.step import AbstractStep
from core.types import RunPlan, StepContext
from typing import Union, List

class CollectNameStep(AbstractStep):
    id = "collect_name"

    def get_context(self, plan: RunPlan) -> StepContext:
        # 1. Yield instructions to your execution loop
        return StepContext(
            prompt="Ask the user for their name. If they provide it, reply 'COLLECTED: [Name]'",
            tools=[]
        )

    def process(self, plan: RunPlan, user_result: str) -> dict:
        # 2. Evaluate the LLM's response
        if "COLLECTED:" in user_result:
            plan.state["name"] = user_result.split("COLLECTED:")[1]
            return {"status": "success"}
            
        # Pause the flow if we need to ask the user a question!
        plan.is_waiting = True
        return {"status": "waiting"}

    def next(self, plan: RunPlan, output: dict) -> Union[str, List[str], None]:
        # 3. Strict Routing (The LLM cannot hallucinate past this)
        if output["status"] == "waiting":
            return "collect_name" # Loop back!
        return "welcome_user" # Advance!
```

### 2. Define Your Flow
```python
from core.flow import AbstractFlow

class OnboardingFlow(AbstractFlow):
    id = "onboarding_flow"
    steps = {
        "collect_name": CollectNameStep,
        # "welcome_user": WelcomeStep
    }
```

### 3. Your Execution Loop (The Developer's Domain)
You wrap Protokol in your own execution environment (CLI, FastAPI, etc.).

```python
from engine.runner import Engine
from core.types import RunPlan

flow = OnboardingFlow()
engine = Engine()
plan = RunPlan(current_step="collect_name")

while not plan.is_terminal and not plan.is_waiting:
    # 1. Ask Protokol what needs to be done
    context = engine.get_context(flow, plan)
    
    # 2. YOU execute the LLM (using any SDK or raw HTTP you want)
    llm_response = my_custom_llm_call(context.prompt) 

    # 3. Feed the result back into Protokol to advance the state machine
    engine.advance(flow, plan, llm_response)
```

---

## 💾 Persistence (Human-in-the-Loop)

Because `RunPlan` is a pure dataclass, pausing a workflow to wait for human input is incredibly simple:

```python
from core.storage import FileStorage

storage = FileStorage(directory=".sessions")

# Save state when the engine pauses
if plan.is_waiting:
    storage.save("session_123", plan)

# Hydrate state perfectly weeks later
resumed_plan = storage.load("session_123")
resumed_plan.is_waiting = False
```

## 🛠️ Advanced Features Built-In
* **Parallel Routing:** Return a `List[str]` from a Step's `next()` method to fan-out execution.
* **Native Retries:** The Engine automatically catches exceptions during `process()` and safely yields the exact same context to let your execution loop retry.
* **Nested Flows:** Flows inherit from Steps, meaning a Flow can be registered as a Step inside another Flow with zero additional config.

---

## 🤝 Contributing
Protokol is designed to be the backbone of enterprise AI routing. Pull requests focusing on execution-agnostic state management, storage adapters (Redis, Postgres), and observability hooks are welcome!

**License:** MIT

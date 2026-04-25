# Quickstart

This guide mirrors the README but focuses on the key steps:

1. **Install** the package.
2. **Define** Steps and Flows.
3. **Run** the engine inside your own execution loop.

```bash
python -m pip install protokol-core
```

### Define a Step

```python
from protokol import AbstractStep, RunPlan, StepContext


class CollectNameStep(AbstractStep):
    id = "collect_name"

    def get_context(self, plan: RunPlan) -> StepContext:
        return StepContext(prompt="Ask the user for their name")

    def process(self, plan: RunPlan, user_result: str) -> dict:
        plan.state["name"] = user_result
        return {"status": "success"}

    def next(self, plan: RunPlan, output: dict):
        plan.is_terminal = True
        return None
```

### Define a Flow & run it

```python
from protokol import AbstractFlow, Engine, RunPlan


class OnboardingFlow(AbstractFlow):
    id = "onboarding_flow"
    steps = {"collect_name": CollectNameStep}


engine = Engine()
flow = OnboardingFlow()
plan = RunPlan(current_step="collect_name")

context = engine.get_context(flow, plan)
print(context.prompt)

mock_response = "Souvik"
engine.advance(flow, plan, mock_response)

print("State:", plan.state)
```
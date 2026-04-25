# Protokol Core Documentation

Welcome to the official documentation for **Protokol**, the ultra-lightweight, enterprise-grade LLM orchestration framework. This site covers the Bring-Your-Own-LLM philosophy, architecture, and real-world usage patterns.

## Highlights

=== "Bring Your Own LLM"
    Protokol is execution-agnostic. It focuses purely on routing and state, letting you plug in any SDK or HTTP client you prefer.

=== "Stateless & Auditable"
    Every flow change is tracked inside the `RunPlan.trace` log. Serialize it to JSON for compliance or cross-service persistence.

=== "Enterprise Ready"
    Human-in-the-loop support, resumable workflows, and zero network dependencies make Protokol ideal for regulated environments.

## Getting Started

Use the navigation to explore the Quickstart guides or jump straight into the API reference.

```bash
python -m pip install protokol-core
```

## Useful Links

- [PyPI](https://pypi.org/project/protokol-core/)
- [GitHub Repository](https://github.com/souvik666/protokol-core)
- [Issue Tracker](https://github.com/souvik666/protokol-core/issues)
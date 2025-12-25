# ai_agents/agent.py
"""
Core abstractions for AI‑Agents Hub.

* ``BaseAgent`` – the abstract base class all agents must inherit from.
* ``EchoAgent`` – a very simple concrete implementation used for demos.
* ``run_workflow`` – a tiny runner that reads a YAML description of a workflow
  and executes the listed agents sequentially.
"""

from __future__ import annotations

import yaml
from typing import Any, Dict, List

from . import register_agent, get_agent_class


class BaseAgent:
    """
    Abstract base class for all agents.

    Subclasses must implement the ``process`` method, which receives an
    arbitrary ``payload`` (normally a ``dict``) and returns a (potentially
    modified) payload.
    """

    def __init__(self, config: Dict[str, Any] | None = None):
        """
        ``config`` holds agent‑specific parameters (e.g., model name,
        temperature, API keys).  Sub‑classes can read what they need.
        """
        self.config = config or {}

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the incoming ``payload`` and return a new payload.

        This method **must** be overridden by concrete agents.
        """
        raise NotImplementedError("Sub‑classes must implement `process`.")


# ----------------------------------------------------------------------
# Example concrete agent
# ----------------------------------------------------------------------
@register_agent
class EchoAgent(BaseAgent):
    """
    A trivial agent that copies the input payload to the output and adds
    a ``message`` field based on the optional ``prefix`` configuration.

    Configuration example:
    ```yaml
    prefix: "🤖 Echo:"
    ```

    This agent is useful for quick sanity checks and as a template
    for building more sophisticated agents.
    """

    def process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        # Preserve everything that came in.
        result = dict(payload)

        # Add a simple echo message.
        prefix = self.config.get("prefix", "Echo:")
        result["message"] = f"{prefix} {payload.get('input', '')}"
        return result


# ----------------------------------------------------------------------
# Tiny workflow runner
# ----------------------------------------------------------------------
def run_workflow(yaml_path: str, initial_payload: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """
    Execute a sequence of agents described in a YAML file.

    The YAML file must contain a top‑level ``agents`` list, where each entry
    is a mapping with the keys:

    * ``name`` – the registered class name (e.g., ``EchoAgent``).
    * ``config`` – optional dict passed to the agent constructor.

    Example workflow (``workflow.yaml``):
    ```yaml
    agents:
      - name: EchoAgent
        config:
          prefix: "[Step 1]"
      - name: EchoAgent
        config:
          prefix: "[Step 2]"
    ```

    Parameters
    ----------
    yaml_path:
        Path to the workflow description.
    initial_payload:
        Optional starting payload; defaults to an empty dict.

    Returns
    -------
    The payload after the last agent has processed it.
    """
    with open(yaml_path, "r", encoding="utf-8") as f:
        spec = yaml.safe_load(f)

    if not isinstance(spec, dict) or "agents" not in spec:
        raise ValueError("Workflow YAML must contain a top‑level `agents` list.")

    payload: Dict[str, Any] = initial_payload or {}

    for idx, agent_def in enumerate(spec["agents"], start=1):
        if not isinstance(agent_def, dict) or "name" not in agent_def:
            raise ValueError(f"Agent definition at position {idx} is malformed.")

        name = agent_def["name"]
        config = agent_def.get("config", {})

        # Retrieve the class from the registry and instantiate it.
        AgentCls = get_agent_class(name)
        agent = AgentCls(config)

        # Run the agent.
        payload = agent.process(payload)

    return payload


# ----------------------------------------------------------------------
# Simple command‑line entry point (optional)
# ----------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    import json
    import sys

    parser = argparse.ArgumentParser(description="Run an AI‑Agents Hub workflow.")
    parser.add_argument("workflow", help="Path to the workflow YAML file.")
    parser.add_argument(
        "--input",
        help="JSON string representing the initial payload (default: empty dict).",
        default="{}",
    )
    args = parser.parse_args()

    try:
        init_payload = json.loads(args.input)
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"Invalid JSON for --input: {exc}\n")
        sys.exit(1)

    try:
        final_payload = run_workflow(args.workflow, init_payload)
    except Exception as exc:  # pragma: no cover
        sys.stderr.write(f"Workflow execution failed: {exc}\n")
        sys.exit(1)

    print(json.dumps(final_payload, indent=2, ensure_ascii=False))

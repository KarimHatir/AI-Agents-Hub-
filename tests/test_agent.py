"""
Unit tests for the core AI‑Agents Hub library.

The tests cover:
* Registry behaviour (registration, lookup, autodiscovery)
* BaseAgent contract enforcement
* Example EchoAgent functionality
* Workflow runner with a tiny temporary YAML file
"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from typing import Dict

import yaml

# Import the package under test
from ai_agents import AGENT_REGISTRY, autodiscover_agents, get_agent_class
from ai_agents.agent import BaseAgent, EchoAgent, run_workflow


class RegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        # Ensure the registry contains at least the built‑in agents
        autodiscover_agents()
        self.original_registry = AGENT_REGISTRY.copy()

    def tearDown(self) -> None:
        # Restore the global registry to its original state
        AGENT_REGISTRY.clear()
        AGENT_REGISTRY.update(self.original_registry)

    def test_echo_agent_is_registered(self) -> None:
        self.assertIn("EchoAgent", AGENT_REGISTRY)
        cls = get_agent_class("EchoAgent")
        self.assertIs(cls, EchoAgent)

    def test_get_unknown_agent_raises(self) -> None:
        with self.assertRaises(KeyError):
            get_agent_class("NonExistentAgent")


class EchoAgentTests(unittest.TestCase):
    def test_default_prefix(self) -> None:
        agent = EchoAgent()
        payload = {"input": "test"}
        result = agent.process(payload)
        self.assertEqual(result["message"], "Echo: test")

    def test_custom_prefix(self) -> None:
        agent = EchoAgent(config={"prefix": ">>"})
        payload = {"input": "hello"}
        result = agent.process(payload)
        self.assertEqual(result["message"], ">> hello")


class WorkflowRunnerTests(unittest.TestCase):
    def write_temp_yaml(self, content: Dict) -> str:
        """Helper that creates a temporary YAML file and returns its path."""
        fd, path = tempfile.mkstemp(suffix=".yaml")
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            yaml.safe_dump(content, f)
        return path

    def test_simple_workflow(self) -> None:
        yaml_content = {
            "agents": [
                {"name": "EchoAgent", "config": {"prefix": "[A]"}},
                {"name": "EchoAgent", "config": {"prefix": "[B]"}},
            ]
        }
        yaml_path = self.write_temp_yaml(yaml_content)

        initial = {"input": "payload"}
        final = run_workflow(yaml_path, initial)

        # The payload should contain the message from the *last* agent
        self.assertEqual(final["message"], "[B] payload")

        # Clean up
        os.remove(yaml_path)

    def test_malformed_yaml_missing_agents_key(self) -> None:
        yaml_content = {"not_agents": []}
        yaml_path = self.write_temp_yaml(yaml_content)
        with self.assertRaises(ValueError):
            run_workflow(yaml_path, {})
        os.remove(yaml_path)

    def test_missing_agent_definition(self) -> None:
        yaml_content = {"agents": [{"config": {}}]}  # no `name`
        yaml_path = self.write_temp_yaml(yaml_content)
        with self.assertRaises(ValueError):
            run_workflow(yaml_path, {})
        os.remove(yaml_path)


# ----------------------------------------------------------------------
# Helper test to ensure BaseAgent raises NotImplementedError when used directly
# ----------------------------------------------------------------------
class BaseAgentContractTest(unittest.TestCase):
    def test_process_not_implemented(self) -> None:
        class Dummy(BaseAgent):
            pass

        dummy = Dummy()
        with self.assertRaises(NotImplementedError):
            dummy.process({})


if __name__ == "__main__":
    # Running the tests via `python -m unittest` is also possible.
    unittest.main()

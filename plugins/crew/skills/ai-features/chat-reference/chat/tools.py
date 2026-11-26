"""The assistant's tools: the only way anything from the system reaches the
model. One home for the set; a tool is a definition, a status line, and a
handler that takes the signed-in user.

A handler filters by that user at the queryset (article 1) and returns
``(result, source)``: plain JSON data, and a label a person can read for
where it came from. It releases only what that user may see, and never a
child's name. Definitions stay byte-stable (prompt caching): no dates or
per-user text in them.

The one tool here is an example to replace."""
import logging
from dataclasses import dataclass
from typing import Callable

logger = logging.getLogger(__name__)

GLOSSARY_SOURCE = "Example glossary 2026-11"
GLOSSARY = {
    "persistent absence": "Missing 10% or more of possible sessions.",
    "severe absence": "Missing 50% or more of possible sessions.",
}


def lookup_term(user, input):
    term = input["term"]
    return {"term": term, "definition": GLOSSARY[term]}, GLOSSARY_SOURCE


@dataclass(frozen=True)
class Tool:
    definition: dict
    label: str
    handler: Callable


TOOLS = {
    "lookup_term": Tool(
        definition={
            "name": "lookup_term",
            "description": "Look up the official definition of an attendance term.",
            "input_schema": {
                "type": "object",
                "properties": {"term": {"type": "string", "enum": sorted(GLOSSARY)}},
                "required": ["term"],
                "additionalProperties": False,
            },
            # The API validates the input against the schema.
            "strict": True,
        },
        label="Looking up the definition…",
        handler=lookup_term,
    ),
}


def definitions():
    """In a fixed order, so the cached prefix never shifts."""
    return [TOOLS[name].definition for name in sorted(TOOLS)]


def labels():
    return {name: tool.label for name, tool in TOOLS.items()}


def runner_for(user):
    """``run(name, input) -> (result, source, is_error)`` for this user. It
    never raises: the reply is already streaming, so a failure is told to
    the model as an error result."""

    def run(name, input):
        tool = TOOLS.get(name)
        if tool is None:
            return {"error": "There is no such tool."}, "", True
        try:
            result, source = tool.handler(user, input)
            return result, source, False
        except Exception as exc:
            # The type only: a message or traceback can quote the input.
            logger.error("Tool %s failed: %s", name, type(exc).__name__)
            return {"error": "That look-up failed. Say you could not check it."}, "", True

    return run

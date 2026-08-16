from pathlib import Path

_PROMPTS = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    return (_PROMPTS / name).read_text(encoding="utf-8")


TIERING_SYSTEM_PROMPT = load_prompt("tiering_agent.prompt.md")
ITINERARY_SYSTEM_PROMPT = load_prompt("itinerary_agent.prompt.md")
DESTINATION_FACTS_SYSTEM_PROMPT = load_prompt("destination_facts_agent.prompt.md")
COLLAB_SYSTEM_PROMPT = load_prompt("collab_agent.prompt.md")

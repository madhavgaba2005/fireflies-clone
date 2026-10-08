import json
from pathlib import Path

from app.events.payloads import CONTRACT_MODELS

CONTRACT = Path(__file__).parents[1] / "contract" / "payloads_v1.schema.json"


def test_payload_schemas_match_committed_contract() -> None:
    """If this fails, the event payload contract changed: update BOTH services and the version."""
    current = {name: model.model_json_schema() for name, model in CONTRACT_MODELS.items()}
    assert current == json.loads(CONTRACT.read_text())

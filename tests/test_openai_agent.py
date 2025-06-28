import sys
import types
from pathlib import Path

# Ensure repository root is on the import path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
# Create a minimal stub for the openai package so that importing the agent does
# not fail in environments without the dependency installed.
sys.modules.setdefault('openai', types.ModuleType('openai'))
sys.modules.setdefault('fitz', types.ModuleType('fitz'))
dotenv_stub = types.ModuleType('dotenv')
dotenv_stub.load_dotenv = lambda *a, **k: None
sys.modules.setdefault('dotenv', dotenv_stub)

from app.processing.openai_agent import parse_json_from_response


def test_parse_unfenced_json():
    text = '{"a": 1, "b": "c"}'
    assert parse_json_from_response(text) == {"a": 1, "b": "c"}


def test_parse_fenced_json():
    text = """```json
{
  "a": 1,
  "b": "c"
}
```"""
    assert parse_json_from_response(text) == {"a": 1, "b": "c"}



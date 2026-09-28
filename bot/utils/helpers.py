import ast
import json
from typing import Any


def curate_dict(value: str | None) -> dict[str, Any] | None:
    if value is None:
        return None

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        try:
            parsed = ast.literal_eval(value)
        except (ValueError, SyntaxError) as exc:
            raise ValueError(
                "La valeur doit être un dictionnaire JSON ou Python valide."
            ) from exc

    if not isinstance(parsed, dict):
        raise ValueError("La valeur doit être un dictionnaire.")

    return parsed

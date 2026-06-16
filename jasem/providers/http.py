"""HTTP helpers shared by the AI providers."""

import json
import re
import urllib.request


def request_json(url, payload, headers, timeout=120):
    """POST a JSON payload and return the decoded JSON response.

    Args:
        url: Endpoint URL.
        payload: JSON-serialisable request body.
        headers: Extra request headers; ``Content-Type`` is added automatically.
        timeout: Socket timeout in seconds.

    Returns:
        The parsed JSON response object.
    """
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **headers},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.load(response)


def extract_json(text):
    """Return the first JSON object found in ``text``.

    Tolerates surrounding prose and ```` ```json ```` code fences so replies
    from chat-style endpoints can be parsed reliably.

    Args:
        text: Raw model reply.

    Returns:
        The decoded JSON object.

    Raises:
        ValueError: If no JSON object can be decoded.
    """
    text = (text or "").strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except ValueError:
        start = text.find("{")
        if start < 0:
            raise
        depth = 0
        for index in range(start, len(text)):
            if text[index] == "{":
                depth += 1
            elif text[index] == "}":
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:index + 1])
        raise

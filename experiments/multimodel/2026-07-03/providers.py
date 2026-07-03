"""Provider-agnostic chat calls for the multi-model campaign. Stdlib only.

Keys come from the environment (XAI_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY,
GEMINI_API_KEY) with a fallback to a `.env` file at the repo root (never committed,
gitignored). Key material never appears in any artifact this module writes.
"""
import json, os, time, urllib.request, urllib.error

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))

MODELS = {
    "grok": dict(provider="xai", model="grok-4-1-fast-non-reasoning"),
    "haiku": dict(provider="anthropic", model="claude-haiku-4-5-20251001"),
    "gpt": dict(provider="openai", model="gpt-4.1-mini"),
    # reasoning tier (gpt-5 family): API rejects temperature/max_tokens; uses
    # max_completion_tokens and default temperature=1 (determinism caveat noted
    # in reasoning-reader/prereg_reasoning.md)
    "gpt5mini": dict(provider="openai_reasoning", model="gpt-5-mini"),
    # gemini-2.5-flash free tier is 20 req/day on this key; flash-lite has its own
    # (much larger) bucket. Substituted 2026-07-03 before any confirmatory gemini
    # scoring — see the dated amendment in v5/prereg.md.
    "gemlite": dict(provider="google", model="gemini-2.5-flash-lite"),
}

# USD per million tokens (input, output), 2026-07 list prices, for cost reporting.
PRICES = {
    "grok": (0.20, 0.50),
    "haiku": (1.00, 5.00),
    "gpt": (0.40, 1.60),
    "gemlite": (0.10, 0.40),
    "gpt5mini": (0.25, 2.00),
}

MAX_OUT = 800


def _key(name):
    v = os.environ.get(name)
    if v:
        return v
    envfile = os.path.join(REPO, ".env")
    if os.path.exists(envfile):
        for line in open(envfile):
            line = line.strip()
            if line.startswith(name + "="):
                return line.split("=", 1)[1].strip()
    raise RuntimeError(f"{name} not found in environment or .env")


# seconds between calls per provider (gemini free-tier RPM limits)
MIN_INTERVAL = {"google": 4.5}
_last_call = {}


def _post(url, headers, body, tag, provider=""):
    gap = MIN_INTERVAL.get(provider, 0)
    if gap:
        wait = _last_call.get(provider, 0) + gap - time.time()
        if wait > 0:
            time.sleep(wait)
    data = json.dumps(body).encode()
    try:
        for attempt in range(5):
            req = urllib.request.Request(url, data=data, headers={
                **headers, "Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=180) as resp:
                    return json.loads(resp.read())
            except urllib.error.HTTPError as e:
                code, detail = e.code, e.read()[:300].decode(errors="replace")
                if (code == 429 or code >= 500) and attempt < 4:
                    time.sleep(20 * (attempt + 1) if code == 429 else 3 * 2 ** attempt)
                    continue
                raise RuntimeError(f"{tag} API error {code}: {detail}")
            except (urllib.error.URLError, TimeoutError):
                if attempt == 4:
                    raise
                time.sleep(3 * 2 ** attempt)
    finally:
        _last_call[provider] = time.time()


def chat(alias, messages):
    """messages: [{role: system|user, content: str}]. Returns (text, usage dict)."""
    cfg = MODELS[alias]
    prov, model = cfg["provider"], cfg["model"]
    if prov == "xai":
        d = _post("https://api.x.ai/v1/chat/completions",
                  {"Authorization": "Bearer " + _key("XAI_API_KEY")},
                  {"model": model, "temperature": 0, "messages": messages}, alias, prov)
        u = d.get("usage", {})
        return d["choices"][0]["message"]["content"], dict(
            prompt=u.get("prompt_tokens", 0), completion=u.get("completion_tokens", 0))
    if prov == "openai_reasoning":
        d = _post("https://api.openai.com/v1/chat/completions",
                  {"Authorization": "Bearer " + _key("OPENAI_API_KEY")},
                  {"model": model, "max_completion_tokens": 4000,
                   "messages": messages}, alias, prov)
        u = d.get("usage", {})
        return d["choices"][0]["message"]["content"], dict(
            prompt=u.get("prompt_tokens", 0), completion=u.get("completion_tokens", 0))
    if prov == "openai":
        d = _post("https://api.openai.com/v1/chat/completions",
                  {"Authorization": "Bearer " + _key("OPENAI_API_KEY")},
                  {"model": model, "temperature": 0, "max_tokens": MAX_OUT,
                   "messages": messages}, alias, prov)
        u = d.get("usage", {})
        return d["choices"][0]["message"]["content"], dict(
            prompt=u.get("prompt_tokens", 0), completion=u.get("completion_tokens", 0))
    if prov == "anthropic":
        sys_txt = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        user = [m for m in messages if m["role"] != "system"]
        body = {"model": model, "max_tokens": MAX_OUT, "temperature": 0,
                "messages": [{"role": m["role"], "content": m["content"]} for m in user]}
        if sys_txt:
            body["system"] = sys_txt
        d = _post("https://api.anthropic.com/v1/messages",
                  {"x-api-key": _key("ANTHROPIC_API_KEY"),
                   "anthropic-version": "2023-06-01"}, body, alias, prov)
        u = d.get("usage", {})
        return "".join(b.get("text", "") for b in d["content"]), dict(
            prompt=u.get("input_tokens", 0), completion=u.get("output_tokens", 0))
    if prov == "google":
        sys_txt = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
        contents = [{"role": "user", "parts": [{"text": m["content"]}]}
                    for m in messages if m["role"] != "system"]
        body = {"contents": contents,
                "generationConfig": {"temperature": 0, "maxOutputTokens": MAX_OUT,
                                     "thinkingConfig": {"thinkingBudget": 0}}}
        if sys_txt:
            body["systemInstruction"] = {"parts": [{"text": sys_txt}]}
        d = _post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                  {"x-goog-api-key": _key("GEMINI_API_KEY")}, body, alias, prov)
        cand = d.get("candidates", [{}])[0]
        text = "".join(p.get("text", "") for p in cand.get("content", {}).get("parts", []))
        u = d.get("usageMetadata", {})
        return text, dict(prompt=u.get("promptTokenCount", 0),
                          completion=u.get("candidatesTokenCount", 0))
    raise ValueError(prov)


def cost_usd(alias, tok):
    pi, po = PRICES[alias]
    return (tok["prompt"] * pi + tok["completion"] * po) / 1e6

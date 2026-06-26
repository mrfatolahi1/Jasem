# AI Backends

Parsing free text into fields is the **only** step in jasem that uses a model.
Everything else — listing, reporting, the dashboard, editing — is pure local
code. You pick a backend with environment variables, and if no model is reachable
jasem still saves your entries using its built-in regex parsing (see
[[Natural Language Input]]).

Three providers are supported, selected with `JASEM_PROVIDER`:

| `JASEM_PROVIDER` | Backend | Needs a key? | Default model |
|------------------|---------|--------------|---------------|
| `ollama` *(default)* | Local [Ollama](https://ollama.com) | no | `qwen2.5:3b` |
| `openai` | Any OpenAI-compatible API | yes | `gpt-4o-mini` |
| `anthropic` | Anthropic (Claude) | yes | `claude-opus-4-8` |

Override the model for any provider with `JASEM_MODEL`.

## Ollama — local, free, private (default)

The default backend. Nothing to configure beyond having Ollama running with a
small model pulled:

```sh
ollama serve
ollama pull qwen2.5:3b
```

jasem talks to Ollama at `http://localhost:11434` by default; point elsewhere
with `OLLAMA_HOST`:

```sh
export OLLAMA_HOST=http://192.168.1.10:11434
```

Use any model you have locally:

```sh
export JASEM_MODEL=llama3.1:8b
```

This keeps everything on your machine — no API key, no network calls off-box.

## OpenAI-compatible APIs

Works with OpenAI itself and any service that speaks the same API — Groq,
OpenRouter, LM Studio, vLLM, and others:

```sh
export JASEM_PROVIDER=openai
export JASEM_API_KEY=sk-...
# For non-OpenAI hosts, set the base URL:
export JASEM_OPENAI_API_BASE=https://openrouter.ai/api/v1
export JASEM_MODEL=gpt-4o-mini          # or the host's model id
```

**Base URL resolution** — jasem reads the first of these that is set:
`JASEM_OPENAI_API_BASE` → `JASEM_OPENAI_BASE_URL` → `OPENAI_BASE_URL` →
`JASEM_API_BASE`. With none set it uses OpenAI's own endpoint.

**API key resolution** — `JASEM_API_KEY` → `OPENAI_API_KEY` → `ANTHROPIC_API_KEY`
(the first that is set). So if you already export `OPENAI_API_KEY`, jasem picks
it up automatically.

### LM Studio / local OpenAI servers

```sh
export JASEM_PROVIDER=openai
export JASEM_OPENAI_API_BASE=http://localhost:1234/v1
export JASEM_API_KEY=lm-studio          # any non-empty string
export JASEM_MODEL=your-local-model
```

## Anthropic (Claude)

```sh
export JASEM_PROVIDER=anthropic
export JASEM_API_KEY=sk-ant-...
export JASEM_MODEL=claude-opus-4-8       # optional; this is the default
```

(`ANTHROPIC_API_KEY` is also accepted as the key.)

## What happens when the backend is down

jasem is designed to never lose an entry because a model is unavailable. If the
backend is unreachable or misconfigured:

* **Tasks** are saved with the raw text as the title and the date parsed by regex.
* **Time** and **spending** fall back to a simple comma format:
  `<duration/amount>, <description>[, <date>][, <tag>]`.

You'll see a short warning, but the add always succeeds. This means you can use
jasem with no AI at all — you just type a touch more structure (commas) and write
clean titles yourself.

```text
# With the backend down, this still works:
jasem track "1h30min, code review, yesterday, work"
jasem acc   "50k, lunch, yesterday, food"
```

## Checking your current backend

`jasem help` prints the resolved provider, model, and file paths at the bottom,
so you can confirm what jasem will actually use:

```text
provider          ollama   (JASEM_PROVIDER: ollama · openai · anthropic)
model             qwen2.5:3b   (JASEM_MODEL)
```

## See also

* [[Configuration]] — the full environment-variable reference
* [[Natural Language Input]] — what the parser and offline fallback extract

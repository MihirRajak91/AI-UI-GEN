# UIAgent

## Professional Project Structure

```text
Tools/
  ir_generation.py              # CLI entrypoint: agentic NL request -> IR JSON (+ React)
  ir_to_react.py                # CLI entrypoint: IR JSON -> TSX
  agent_api.py                  # FastAPI adapter for session-based conversation
  ir_structure.py               # Backward-compatible schema export
  generated_ir.json             # Generated IR output
  generated_app.tsx             # Generated React output
  sessions/                     # Persisted conversation sessions and traces
  ir_pipeline/
    agents/                     # Specialist agent modules
    graph/                      # LangGraph nodes/routing/graph definition
    llm/
      client.py                 # AWS Bedrock Anthropic/LangChain model setup
    prompts/
      ir_generation.py          # IR generation prompt builders
      react_generation.py       # React generation prompt builder
      frontend_design_policy.py # Professional UI critic policy
      ui_critic.py              # Critic prompt builder
    schemas/
      ir_bundle.py              # Pydantic IRBundle schema
      conversation.py           # Session/turn/coverage/critic contracts
      graph_state.py            # Typed LangGraph state
      api_models.py             # FastAPI request/response DTOs
    services/
      ir_generation_service.py  # IR generation orchestration
      react_generation_service.py # React generation orchestration
      conversation_service.py   # Graph-backed conversation APIs
      session_store.py          # Session persistence
      trace_store.py            # Node transition traces
    utils/
      extractors.py             # JSON/code block extraction helpers
      normalization.py          # LLM output normalization helpers
      ids.py                    # Session id helpers
      time_utils.py             # UTC timestamp helpers
docs/
  agentic-langgraph/            # Micro-step migration docs and runbooks
tests/
  agent/ api/ cli/              # Unit/API/CLI tests
```

## Run

From repo root:

```bash
uv run python Tools/ir_generation.py --agentic
uv run python Tools/ir_to_react.py
uv run python Tools/full_pipeline_cli.py
uv run python Tools/end_user_chat.py
```

`full_pipeline_cli.py` runs the complete chat -> IR -> React flow with full transparency:
- slot-by-slot requirement coverage (met vs remaining)
- assumptions and UI critic output
- node trace events for each turn
- model assignment and artifact paths
- when coverage gate passes: explicit `generate` vs `refine` action choice

`end_user_chat.py` is the simplified end-user script:
- natural chat with follow-up questions
- explicit `generate` or `refine` step when ready
- auto-generates IR + React artifacts after `generate`
- fast by default (skips heavy critic pass); enable full critic with `--with-critic`

### Agentic CLI flags

```bash
uv run python Tools/ir_generation.py --agentic --session-id <session_id>
uv run python Tools/ir_generation.py --no-agentic
```

Default agentic flow:
- multi-turn requirement capture
- per-turn UI critic recommendations
- confirmation gate
- IR generation
- auto React generation

Bedrock/Claude config is read from `.env` (or environment variables):

```dotenv
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_SESSION_TOKEN=...  # optional
AWS_REGION=us-east-1
MODEL_DEFAULT=global.anthropic.claude-sonnet-4-5-20250929-v1:0
MODEL_ORCHESTRATOR=global.anthropic.claude-sonnet-4-5-20250929-v1:0
MODEL_EXTRACTOR=global.anthropic.claude-haiku-4-5-20251001-v1:0
MODEL_CLARIFIER=global.anthropic.claude-sonnet-4-5-20250929-v1:0
MODEL_CRITIC=global.anthropic.claude-sonnet-4-6
MODEL_SUMMARIZER=global.anthropic.claude-sonnet-4-5-20250929-v1:0
MODEL_IR_GENERATOR=global.anthropic.claude-sonnet-4-6
MODEL_REACT_COMPILER=global.anthropic.claude-sonnet-4-6
```

Opus models are explicitly rejected in validation for this project.

`ir_to_react.py` now writes generated React code directly to:

- `ui-compiler-poc/frontend/src/App.tsx`

so the frontend can be run immediately without manual copying.

## API

Start the API:

```bash
uv run uvicorn --app-dir Tools agent_api:app --reload
```

Endpoints:
- `POST /sessions`
- `POST /sessions/{session_id}/messages`
- `POST /sessions/{session_id}/confirm`
- `GET /sessions/{session_id}`

## Logs

- Log file is maintained automatically at:
  - `Tools/logs/uia.log`
- The file is rotated automatically (max ~1MB per file, 5 backups).

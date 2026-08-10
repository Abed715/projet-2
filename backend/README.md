# jarvis (backend)

FastAPI/AsyncIO backend for the JARVIS assistant. See the repository root
[`ARCHITECTURE.md`](../ARCHITECTURE.md) and [`ROADMAP.md`](../ROADMAP.md) for
the full design and build order.

## Layout

Each subpackage under `src/jarvis/` is an independent module with a narrow
public interface exported from its `__init__.py`. See each module's own
`README.md` for its responsibility, current status, and build phase.

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
ruff check src tests
mypy src
uvicorn jarvis.api.app:create_app --factory --reload
```

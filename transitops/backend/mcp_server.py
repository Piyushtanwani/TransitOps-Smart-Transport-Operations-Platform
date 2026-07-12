"""TransitOps MCP server (T2 stretch, BE-16).

Exposes the read-only AI tool registry (`app.services.ai.tools.TOOLS`) over stdio
so any MCP client (e.g. Claude Desktop) can query the fleet. Runs with a service
role equivalent to `financial_analyst` (broadest read scope) — per-user MCP auth
is the production follow-up, documented in README.md.

Run:  python mcp_server.py
"""
from __future__ import annotations

import inspect
from types import SimpleNamespace

from fastmcp import FastMCP

from app.db.session import SessionLocal
from app.services.ai.tools import TOOLS

mcp = FastMCP("TransitOps")

# Service-role identity: read scope equivalent to financial_analyst (broadest).
_SERVICE_USER = SimpleNamespace(role=SimpleNamespace(value="financial_analyst"))

_JSON_TO_PY = {"string": str, "integer": int, "number": float, "boolean": bool}


def _annotation(spec: dict):
    return _JSON_TO_PY.get(spec.get("type"), str) | None


def _build_signature(properties: dict) -> inspect.Signature:
    """fastmcp requires real typed params (no **kwargs) — synthesize from the schema."""
    params = [
        inspect.Parameter(name, inspect.Parameter.KEYWORD_ONLY, default=None,
                           annotation=_annotation(spec))
        for name, spec in properties.items()
    ]
    return inspect.Signature(params)


def _register(name: str) -> None:
    tool = TOOLS[name]
    properties = tool.parameters.get("properties", {})

    def _handler(**kwargs):
        db = SessionLocal()
        try:
            return tool.executor(db, _SERVICE_USER, **kwargs)
        finally:
            db.close()

    _handler.__name__ = name
    _handler.__doc__ = tool.description
    _handler.__signature__ = _build_signature(properties)
    _handler.__annotations__ = {n: _annotation(spec) for n, spec in properties.items()}
    mcp.tool(name=name, description=tool.description)(_handler)


for _name in TOOLS:
    _register(_name)


if __name__ == "__main__":
    mcp.run()

init:
    uv sync
    uv run rqstr gen-schema > .rqstr_schema.json


test: init
    uv run pytest

example:
    uv run rqstr do ./examples/*
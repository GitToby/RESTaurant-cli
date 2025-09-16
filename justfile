api-test:
    uv run restaurant do examples/*

test-pw:
    PASTMAN_PASSWORD=test123 uv run restaurant do examples/tests/secrets.rest.yml

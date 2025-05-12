# RESTurant

> A dead simple CLI to run HTTP requests from YAML collection files.

RESTurant is a lightweight, developer-friendly API testing tool focused on simplicity and CI integration. Define your API requests in YAML and run comprehensive tests from your command line or CI pipeline.

## Features

- **Simple CLI Interface**: Test APIs with minimal commands
- **Declarative Testing**: Define requests and expected responses in YAML
- **CI-Focused**: Run API tests separately from application code
- **Automatic Discovery**: Scan directories for test collections
- **Cross-Platform**: Works on Linux, macOS, and Windows

## Coming Soon
- Environment variable interpolation in requests
- Response dumping to files for detailed analysis
- benchmark endpoints over n requests

## Installation

```bash
# Install via your package manager of choice
pip install restaurant-cli
```

## Command Reference

```
Usage: RESTaurant COMMAND
A dead simple CLI to run HTTP requests from a collection file.
╭─ Commands ─────────────────────────────────────────────────────────────────────────────────────────────╮
│ gen-schema Generate the schema for the request collection.                                             │
│ run        Scan for request collections in child dirs and run the requests in them.                    │
│ --help -h  Display this message and exit.                                                              │
│ --version  Display application version.                                                                │
╰────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Quick Start

1. Create a `.rest.yml` file (e.g. `github.rest.yml`):

```yaml
# yaml-language-server: $schema=../.request_collection_schema.json
title: "GitHub API Collection"
description: "A collection of example requests for the GitHub API"
headers:
  Accept: "application/vnd.github.v3+json"
  User-Agent: "API-Test-Client"
requests:
  getUserProfile:
    method: GET
    url: "https://api.github.com/users/octocat"
    assert:
      status_code: 200
    soft_timeout_s: 3.0
  getZenMessage:
    method: GET
    url: "https://api.github.com/zen"
    assert:
      status_code: 200
  getRepository:
    method: GET
    url: "https://api.github.com/repos/octocat/hello-world"
    assert:
      status_code: 200
  searchRepositories:
    method: GET
    url: "https://api.github.com/search/repositories"
    extra_headers:
      Accept: "application/vnd.github.v3.text-match+json"
    body:
      q: "tetris"
      sort: "stars"
      order: "desc"
    assert:
      status_code: 200
```

2. Run your tests:

```bash
# Run all request collections in the current directory and subdirectories
restaurant run
```

## Example Output

When you run the command, RESTurant will scan for `.rest.yml` files and execute the requests in them:

```
No input files provided, scanning for files in `/Users/toby/dev/projects/RESTaurant/**/*.rest.yml`
Found 3 collection files.
[1/3] Loading /Users/toby/dev/projects/RESTaurant/resources/github.rest.yml... Done.
[1/3] GitHub API Collection
[1/3] Running 4 requests...
[1/3] ✅ GET https://api.github.com/users/octocat 200 (0:00:00.056743)
[1/3] ✅ GET https://api.github.com/zen 200 (0:00:00.055040)
[1/3] ✅ GET https://api.github.com/repos/octocat/hello-world 200 (0:00:00.054677)
[1/3] ❌ GET https://api.github.com/search/repositories 422 expected 403 (0:00:00.066147)
[2/3] Loading /Users/toby/dev/projects/RESTaurant/resources/example.rest.yml... Done.
[2/3] Example REST API testing
[2/3] Running 3 requests...
[2/3] ✅ GET https://api.ipify.org/ 200 (0:00:00.119540)
[2/3] ❌ POST https://api.ipify.org/ 520 expected 403 (0:00:00.468796)
[2/3] ✅ GET https://pastebin.com/favicon.ico 200 (0:00:00.062359)
[3/3] Loading /Users/toby/dev/projects/RESTaurant/resources/jsonplaceholder.rest.yml... Done.
[3/3] JSON Placeholder API Collection
[3/3] Running 5 requests...
[3/3] ✅ GET https://jsonplaceholder.typicode.com/posts 200 (0:00:00.064326)
[3/3] ✅ GET https://jsonplaceholder.typicode.com/posts/1 200 (0:00:00.062546)
[3/3] ✅ POST https://jsonplaceholder.typicode.com/posts 201 (0:00:00.296911)
[3/3] ✅ PUT https://jsonplaceholder.typicode.com/posts/1 200 (0:00:00.143119)
[3/3] ✅ DELETE https://jsonplaceholder.typicode.com/posts/1 200 (0:00:00.145088)
```

## Configuration File Format

The `.rest.yml` file structure:

```yaml
# Collection metadata
title: "API Collection Title"
description: "Description of this collection"

# Global headers applied to all requests
headers:
  Accept: "application/json"
  User-Agent: "RESTurant-Client"

# Individual request definitions
requests:
  requestName:
    method: GET                           # HTTP method
    url: "https://api.example.com/path"   # Full URL
    extra_headers:                        # Additional headers for this request
      Authorization: "Bearer token123"
    body:                                 # Request body (as JSON)
      key: "value"
    assert:
      status_code: 200                    # Expected status code
    soft_timeout_s: 5.0                   # Timeout in seconds
```

## Schema Generation

RESTurant can generate a JSON schema for your collection files:

```bash
# Generate schema
restaurant gen-schema > .request_collection_schema.json
```

This schema can be used with editor extensions like VS Code's YAML Language Server for validation and autocompletion.

## CI Integration

### GitHub Actions Example

```yaml
# .github/workflows/api-tests.yml
name: API Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Install RESTurant
        run: pip install restaurant-cli
      - name: Run API tests
        run: restaurant run
```

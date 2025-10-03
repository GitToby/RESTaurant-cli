# rqstr

A simple CLI tool to execute HTTP requests from YAML collection files.

rqstr is a lightweight API testing tool that lets you define HTTP requests in YAML files and execute them from the command line. Perfect for API testing, monitoring, and CI/CD pipelines.

## Features

- **Declarative YAML format** - Define requests with clear, readable syntax
- **Automatic discovery** - Scans directories for `.rest.yml` files
- **Request validation** - Built-in assertions for status codes and timeouts
- **Benchmarking support** - Run requests multiple times for performance testing
- **Environment variables** - Template variables in request definitions
- **JSON schema validation** - IDE support with autocompletion and validation
- **Detailed output** - Clear success/failure reporting with timing information

## Installation

```bash
pip install rqstr-cli
```

## Quick Start

1. Create a `.rest.yml` file:

```yaml
title: "API Tests"
headers:
  User-Agent: "rqstr-client"

requests:
  getUser:
    method: GET
    url: "https://api.github.com/users/octocat"
    assert:
      status_code: 200
      soft_timeout_s: 3.0

  searchRepos:
    method: GET
    url: "https://api.github.com/search/repositories"
    query_params:
      q: "python"
      sort: "stars"
    assert:
      status_code: 200
```

2. Run your requests:

```bash
# Run all .rest.yml files in current directory and subdirectories
rqstr run

# Run specific files
rqstr run api-tests.rest.yml another-test.rest.yml
```

## Commands

- `rqstr run [files...]` - Execute request collections
- `rqstr gen-schema` - Generate JSON schema for YAML validation
- `rqstr example-collection [name]` - Create example collection file

## YAML Format

```yaml
# yaml-language-server: $schema=../.rqstr_schema.json

# Collection metadata
title: "My API Tests"
description: "Optional description"

# Global headers for all requests
headers:
  Accept: "application/json"

# Global Auth for all requests
auth:
  token: ${API_TOKEN}

# Request definitions
requests:
  requestName:
    method: GET # HTTP method
    url: "https://api.example.com" # Request URL

    # Optional: additional headers
    extra_headers:
      Content-Type: "application/json"

    # Optional: query parameters
    query_params:
      param1: "value"
      param2: ["multiple", "values"]

    # Optional: JSON body
    body:
      key: "value"

    # Optional: assertions
    assert:
      status_code: 200 # Expected status code
      soft_timeout_s: 5.0 # Request timeout

    # Optional: benchmark (run N times)
    benchmark: 10
```

## Environment Variables

Use `${VAR_NAME}` syntax to reference environment variables with optional defaults:

```yaml
headers:
  Authorization: "Bearer ${API_TOKEN}"
  Custom-Header: "${CUSTOM_VALUE:-default_value}"
```

## Schema Validation

Generate a JSON schema for IDE support:

```bash
rqstr gen-schema > .request_collection_schema.json
```

Then add to your YAML files:

```yaml
# yaml-language-server: $schema=./.request_collection_schema.json
title: "My Collection"
# ... rest of your configuration
```

## Example Output

```
$ rqstr do ./examples/*
Found 4 collection files.

Loading examples/example.rest.yml... Done.
My API Tests - Running 1 requests... Done.
 [1/1] - requestName 0/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 0.999s
 [1/1] - requestName 1/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 1.025s
 [1/1] - requestName 2/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 0.995s
 [1/1] - requestName 3/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 1.009s
 [1/1] - requestName 4/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 1.017s
 [1/1] - requestName 5/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 1.008s
 [1/1] - requestName 6/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 0.995s
 [1/1] - requestName 7/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 0.996s
 [1/1] - requestName 8/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 0.985s
 [1/1] - requestName 9/10     | ✅ GET   https://example.com/?param1=value&param2=multiple&param2=values (200) in 1.000s
Files written to '/Users/toby/dev/projects/rqstr-cli/out/My API Tests/2025-10-03/16:15:22'

Loading examples/github.rest.yml... Done.
Github Requests - Running 4 requests... Done.
 [1/4] - getUserProfile       | ✅ GET   https://api.github.com/users/octocat (200) in 0.206s
 [2/4] - getZenMessage        | ✅ GET   https://api.github.com/zen (200) in 0.124s
 [3/4] - getRepository        | ✅ GET   https://api.github.com/repos/octocat/hello-world (200) in 0.210s
 [4/4] - searchRepositories   | ❌ GET   https://api.github.com/search/repositories (422) in 0.130s
Files written to '/Users/toby/dev/projects/rqstr-cli/out/Github Requests/2025-10-03/16:15:22'

Loading examples/jsonplaceholder.rest.yml... Done.
JSON Placeholder API Collection - Running 5 requests... Done.
 [1/5] - getAllPosts          | ✅ GET   https://jsonplaceholder.typicode.com/posts (200) in 0.361s
 [2/5] - getSinglePost        | ✅ GET   https://jsonplaceholder.typicode.com/posts/1 (200) in 0.030s
 [3/5] - createPost           | ✅ POST  https://jsonplaceholder.typicode.com/posts (201) in 0.116s
 [4/5] - updatePost           | ✅ PUT   https://jsonplaceholder.typicode.com/posts/1 (200) in 0.111s
 [5/5] - deletePost           | ✅ DELETE https://jsonplaceholder.typicode.com/posts/1 (200) in 0.108s
Files written to '/Users/toby/dev/projects/rqstr-cli/out/JSON Placeholder API Collection/2025-10-03/16:15:22'

Loading examples/openweather.rest.yml... Done.
OpenWeatherMap API Collection - Running 3 requests... Done.
 [1/3] - getCurrentWeather    | ❌ GET   https://api.openweathermap.org/data/2.5/weather (401) in 0.146s
 [2/3] - getForecast          | ❌ GET   https://api.openweathermap.org/data/2.5/forecast (401) in 0.044s
 [3/3] - getAirPollution      | ❌ GET   https://api.openweathermap.org/data/2.5/air_pollution (401) in 0.046s
Files written to '/Users/toby/dev/projects/rqstr-cli/out/OpenWeatherMap API Collection/2025-10-03/16:15:22'
```

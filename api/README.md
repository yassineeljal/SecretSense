# SecretSense local API

Install `./core[api]` from the repository root and start one loopback worker:

```sh
python -m uvicorn api.main:app --host 127.0.0.1 --workers 1 --no-access-log --no-proxy-headers --limit-concurrency 16 --backlog 32 --timeout-keep-alive 5
```

See [the API/site guide](../docs/api-and-web.md) for endpoints, response semantics,
byte/rate/concurrency/deadline limits, browser behavior, and tests. This API is a
local demonstration, with no authentication or public hosting configuration.

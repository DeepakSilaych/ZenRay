# SDK Configuration

The SDK reads configuration from environment variables by default, and you can override most values in `xray.init(...)`.

## Environment variables

- `XRAY_ENDPOINT`: backend URL (default: `http://localhost:8000`)
- `XRAY_DISABLED`: disable tracing (`true`/`false`)
- `XRAY_SAMPLE_RATE`: float 0..1
- `XRAY_BATCH_SIZE`: flush batch size
- `XRAY_FLUSH_INTERVAL`: flush interval (seconds)
- `XRAY_TOP_K`: number of top candidates captured for `top_kept`/`top_dropped`

## `xray.init(...)`

Use code to override env:

- `xray.init(endpoint=...)`
- `xray.init(disabled=...)`
- `xray.init(sample_rate=...)`
- `xray.init(top_k=...)`

## Related docs

- Candidate storage & what it powers in the UI: [`../backend/storage.md`](../backend/storage.md)
- SDK behavior overview: [`overview.md`](./overview.md)

## Where to make changes

- Config definition + env parsing: `sdk/xray/config.py`
- `xray.init(...)` behavior: `sdk/xray/config.py`
- “top kept/dropped” capture count: `sdk/xray/context.py` (decorator path) and `sdk/xray/candidates.py` (legacy path)



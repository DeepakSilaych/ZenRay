# SDK Examples

These examples live in `sdk/examples/` and are intended to generate realistic traces for the UI.

## Suggested run order

- Minimal demo (small): `sdk/examples/minimal_api_demo.py`
- E-commerce search (medium/large): `sdk/examples/ecommerce_search.py`
- RAG retrieval (LLM-style): `sdk/examples/rag_document_retrieval.py`
- Recommendation system (large): `sdk/examples/recommendation_system.py`
- Content moderation batch (large): `sdk/examples/content_moderation.py`

## Tips

- Set `XRAY_ENDPOINT` to point at your backend.
- Consider setting `XRAY_TOP_K` when you want more “top kept/dropped” samples to show in the UI.

See configuration: [`configuration.md`](./configuration.md)

## Where to make changes

- Add new example pipelines: `sdk/examples/`
- If an example’s “candidate identity” doesn’t trace well, ensure items have stable IDs (usually `id` field) so `xray.drop/xray.score` can associate data.

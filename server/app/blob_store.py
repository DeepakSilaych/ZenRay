import json
from pathlib import Path
from typing import Any, Optional

BLOB_DIR = Path("data/blobs")

def init_blob_store():
    BLOB_DIR.mkdir(parents=True, exist_ok=True)

def _blob_path(blob_id: str) -> Path:
    # Use first 2 chars as subdirectory for better filesystem performance
    subdir = blob_id[:2] if len(blob_id) >= 2 else "00"
    return BLOB_DIR / subdir / f"{blob_id}.json"

def save_blob(blob_id: str, data: Any) -> str:
    """Save data to blob store, returns the blob path."""
    path = _blob_path(blob_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, default=str))
    return str(path)

def load_blob(blob_id: str) -> Optional[Any]:
    """Load data from blob store."""
    path = _blob_path(blob_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())

def delete_blob(blob_id: str) -> bool:
    """Delete blob, returns True if deleted."""
    path = _blob_path(blob_id)
    if path.exists():
        path.unlink()
        return True
    return False

def blob_exists(blob_id: str) -> bool:
    return _blob_path(blob_id).exists()

# --- Candidate Set helpers ---

def save_candidate_set(step_id: str, candidate_set: dict) -> str:
    """Save candidate set, returns blob reference."""
    blob_id = f"cs_{step_id}"
    return save_blob(blob_id, candidate_set)

def load_candidate_set(step_id: str) -> Optional[dict]:
    """Load candidate set for a step."""
    blob_id = f"cs_{step_id}"
    return load_blob(blob_id)

# --- Artifact helpers ---

def save_artifact(artifact_id: str, content: Any) -> str:
    """Save artifact, returns blob reference."""
    blob_id = f"art_{artifact_id}"
    return save_blob(blob_id, content)

def load_artifact(artifact_id: str) -> Optional[Any]:
    """Load artifact content."""
    blob_id = f"art_{artifact_id}"
    return load_blob(blob_id)

def list_artifacts_for_step(step_id: str) -> list[dict]:
    """List all artifacts for a step (by scanning blob store)."""
    # This is a simple implementation; in production you'd use an index
    artifacts = []
    prefix = f"art_{step_id}_"
    for subdir in BLOB_DIR.iterdir():
        if subdir.is_dir():
            for blob_file in subdir.glob("*.json"):
                if blob_file.stem.startswith(prefix):
                    artifact_id = blob_file.stem.replace("art_", "")
                    artifacts.append({
                        "artifact_id": artifact_id,
                        "blob_path": str(blob_file),
                    })
    return artifacts


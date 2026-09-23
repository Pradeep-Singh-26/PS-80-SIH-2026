"""Lightweight File-Based MLOps Model Registry (Track B - Task 11 / Step 7).

Provides versioning, artifact serialization, SHA-256 checksum integrity verification,
feature schema validation, active model tagging, and audit-logged rollback for bias correction
and uncertainty models.

Directory Layout:
    <registry_root>/
        <model_name>/
            v001/
                model.joblib
                metadata.json
            v002/
                model.joblib
                metadata.json
            active.json
"""

from datetime import datetime, timezone
import hashlib
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Tuple

import joblib

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("model_registry")


def compute_file_sha256(file_path: Path | str) -> str:
    """Compute SHA-256 cryptographic checksum of a file on disk."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


class ModelRegistry:
    """Filesystem-based lightweight model registry with cryptographic checksums and schema validation."""

    def __init__(self, registry_root: Path | str = "models"):
        self.registry_root = Path(registry_root)
        self.registry_root.mkdir(parents=True, exist_ok=True)

    def _get_model_dir(self, model_name: str) -> Path:
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", model_name.strip().lower())
        return self.registry_root / clean_name

    def _get_active_file(self, model_name: str) -> Path:
        return self._get_model_dir(model_name) / "active.json"

    def _generate_next_version(self, model_name: str) -> str:
        model_dir = self._get_model_dir(model_name)
        if not model_dir.exists():
            return "v001"
        existing_versions = []
        for p in model_dir.iterdir():
            if p.is_dir() and re.match(r"^v\d{3,}$", p.name):
                try:
                    num = int(p.name[1:])
                    existing_versions.append(num)
                except ValueError:
                    pass
        if not existing_versions:
            return "v001"
        next_num = max(existing_versions) + 1
        return f"v{next_num:03d}"

    def register_model(
        self,
        model_name: str,
        model_obj: Any,
        model_type: str,
        feature_names: List[str],
        version: Optional[str] = None,
        hyperparameters: Optional[Dict[str, Any]] = None,
        metrics: Optional[Dict[str, float]] = None,
        training_start_date: Optional[str] = None,
        training_end_date: Optional[str] = None,
        training_sample_count: Optional[int] = None,
        validation_start_date: Optional[str] = None,
        validation_end_date: Optional[str] = None,
        data_status: str = "synthetic_fixture",
        git_commit_sha: Optional[str] = None,
        notes: Optional[str] = None,
        set_as_active: bool = False,
    ) -> Dict[str, Any]:
        """Register and serialize a trained model artifact with rich metadata.

        Parameters
        ----------
        model_name : str
            Name/identifier of the model family (e.g. 'bias_corrector_ml').
        model_obj : Any
            Python model object to serialize.
        model_type : str
            Model class/algorithm name.
        feature_names : List[str]
            Exact list of expected feature columns in order.
        version : Optional[str]
            Explicit version tag (e.g. 'v001'). If None, automatically incremented.
        hyperparameters : Optional[Dict[str, Any]]
            Model configuration / training hyperparameters.
        metrics : Optional[Dict[str, float]]
            Evaluation metrics (e.g. MAE, RMSE, Brier Score).
        training_start_date : Optional[str]
            Start date of training dataset.
        training_end_date : Optional[str]
            End date of training dataset.
        training_sample_count : Optional[int]
            Number of training samples.
        validation_start_date : Optional[str]
            Start date of held-out validation dataset.
        validation_end_date : Optional[str]
            End date of held-out validation dataset.
        data_status : str, default='synthetic_fixture'
            'synthetic_fixture' or 'operational'.
        git_commit_sha : Optional[str]
            Git commit hash at time of training.
        notes : Optional[str]
            Engineering/scientific notes.
        set_as_active : bool, default=False
            Whether to immediately tag this version as active.

        Returns
        -------
        Dict[str, Any]
            The saved metadata dictionary.
        """
        if not model_name or not model_name.strip():
            raise ValueError("model_name cannot be empty.")
        if not feature_names:
            raise ValueError("feature_names list cannot be empty.")

        model_dir = self._get_model_dir(model_name)
        model_dir.mkdir(parents=True, exist_ok=True)

        if version is None:
            ver_str = self._generate_next_version(model_name)
        else:
            if not re.match(r"^v\d{3,}$", version):
                raise ValueError(f"Invalid version format '{version}'. Expected format like 'v001', 'v002'.")
            ver_str = version

        ver_dir = model_dir / ver_str
        if ver_dir.exists() and (ver_dir / "model.joblib").exists():
            raise FileExistsError(f"Version '{ver_str}' for model '{model_name}' already exists.")

        ver_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = ver_dir / "model.joblib"
        metadata_path = ver_dir / "metadata.json"

        # 1. Serialize model artifact
        joblib.dump(model_obj, artifact_path, compress=3)

        # 2. Compute checksum
        sha256_hash = compute_file_sha256(artifact_path)

        # 3. Assemble metadata
        metadata = {
            "model_name": model_name,
            "model_type": model_type,
            "version": ver_str,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "feature_names": list(feature_names),
            "feature_count": len(feature_names),
            "training_start_date": training_start_date,
            "training_end_date": training_end_date,
            "training_sample_count": training_sample_count,
            "validation_start_date": validation_start_date,
            "validation_end_date": validation_end_date,
            "metrics": metrics or {},
            "hyperparameters": hyperparameters or {},
            "data_status": data_status,
            "git_commit_sha": git_commit_sha,
            "artifact_rel_path": str(artifact_path.relative_to(self.registry_root)),
            "artifact_sha256": sha256_hash,
            "notes": notes,
        }

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        logger.info(f"Registered model '{model_name}' version '{ver_str}' [SHA256: {sha256_hash[:8]}...]")

        if set_as_active or not self._get_active_file(model_name).exists():
            self.set_active(model_name, ver_str)

        return metadata

    def list_versions(self, model_name: str) -> List[Dict[str, Any]]:
        """List all registered versions and metadata for a given model name."""
        model_dir = self._get_model_dir(model_name)
        if not model_dir.exists():
            return []

        active_ver = self.get_active(model_name)
        versions = []

        for p in sorted(model_dir.iterdir()):
            if p.is_dir() and (p / "metadata.json").exists():
                try:
                    with open(p / "metadata.json", "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    meta["is_active"] = (meta.get("version") == active_ver)
                    versions.append(meta)
                except Exception as e:
                    logger.warning(f"Corrupted metadata in {p}: {e}")

        return versions

    def get_metadata(self, model_name: str, version: Optional[str] = None) -> Dict[str, Any]:
        """Fetch metadata for a specific or active model version."""
        if version is None:
            version = self.get_active(model_name)
            if version is None:
                raise ValueError(f"No active version found for model '{model_name}'.")

        meta_file = self._get_model_dir(model_name) / version / "metadata.json"
        if not meta_file.exists():
            raise FileNotFoundError(f"Metadata not found for model '{model_name}' version '{version}'.")

        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Corrupted metadata JSON for '{model_name}' version '{version}': {e}")

    def load_model(
        self,
        model_name: str,
        version: Optional[str] = None,
        validate_schema: bool = True,
        expected_features: Optional[List[str]] = None,
        verify_checksum: bool = True,
    ) -> Tuple[Any, Dict[str, Any]]:
        """Load a model artifact with checksum and feature schema validation.

        Parameters
        ----------
        model_name : str
            Name of model.
        version : Optional[str]
            Version to load. If None, loads active version.
        validate_schema : bool, default=True
            Whether to validate feature schema against expected_features.
        expected_features : Optional[List[str]]
            List of expected feature names to verify against.
        verify_checksum : bool, default=True
            Whether to verify SHA-256 artifact integrity against metadata.

        Returns
        -------
        Tuple[Any, Dict[str, Any]]
            (deserialized_model_object, metadata_dict)
        """
        metadata = self.get_metadata(model_name, version)
        ver_str = metadata["version"]
        ver_dir = self._get_model_dir(model_name) / ver_str
        artifact_path = ver_dir / "model.joblib"

        if not artifact_path.exists():
            raise FileNotFoundError(f"Model artifact missing at: {artifact_path}")

        # 1. Verify Checksum
        if verify_checksum:
            expected_hash = metadata.get("artifact_sha256")
            if expected_hash:
                actual_hash = compute_file_sha256(artifact_path)
                if actual_hash != expected_hash:
                    raise ValueError(
                        f"Checksum mismatch for '{model_name}:{ver_str}'! "
                        f"Expected: {expected_hash}, Actual: {actual_hash}"
                    )

        # 2. Validate Schema
        if validate_schema and expected_features is not None:
            saved_features = metadata.get("feature_names", [])
            if list(saved_features) != list(expected_features):
                raise ValueError(
                    f"Feature schema mismatch for '{model_name}:{ver_str}'.\n"
                    f"Expected ({len(expected_features)}): {expected_features}\n"
                    f"Saved ({len(saved_features)}): {saved_features}"
                )

        # 3. Deserialize Artifact
        model_obj = joblib.load(artifact_path)
        logger.info(f"Loaded model '{model_name}' version '{ver_str}' successfully.")
        return model_obj, metadata

    def set_active(self, model_name: str, version: str) -> Dict[str, Any]:
        """Mark a specific version as active and record in audit history."""
        # Verify version exists
        _ = self.get_metadata(model_name, version)

        active_file = self._get_active_file(model_name)
        history = []

        if active_file.exists():
            try:
                with open(active_file, "r", encoding="utf-8") as f:
                    curr_active_data = json.load(f)
                    history = curr_active_data.get("history", [])
                    prev_active = curr_active_data.get("active_version")
                    if prev_active and prev_active != version:
                        history.append({
                            "version": prev_active,
                            "deactivated_at": datetime.now(timezone.utc).isoformat(),
                        })
            except Exception:
                pass

        active_data = {
            "model_name": model_name,
            "active_version": version,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "history": history,
        }

        with open(active_file, "w", encoding="utf-8") as f:
            json.dump(active_data, f, indent=2)

        logger.info(f"Model '{model_name}' active version set to: {version}")
        return active_data

    def get_active(self, model_name: str) -> Optional[str]:
        """Retrieve the currently active version string for a model."""
        active_file = self._get_active_file(model_name)
        if not active_file.exists():
            return None
        try:
            with open(active_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("active_version")
        except Exception:
            return None

    def rollback(self, model_name: str) -> Dict[str, Any]:
        """Roll back the active model to the previously active version.

        Does not delete any version artifacts.
        """
        active_file = self._get_active_file(model_name)
        if not active_file.exists():
            raise ValueError(f"No active configuration found for model '{model_name}'.")

        with open(active_file, "r", encoding="utf-8") as f:
            active_data = json.load(f)

        current_version = active_data.get("active_version")
        history = active_data.get("history", [])

        if not history:
            raise ValueError(f"Cannot rollback '{model_name}': no previous version in history.")

        # Pop previous active version
        last_entry = history.pop()
        target_version = last_entry["version"]

        # Validate target version still exists on disk
        self.get_metadata(model_name, target_version)

        new_active_data = {
            "model_name": model_name,
            "active_version": target_version,
            "activated_at": datetime.now(timezone.utc).isoformat(),
            "history": history,
            "rolled_back_from": current_version,
        }

        with open(active_file, "w", encoding="utf-8") as f:
            json.dump(new_active_data, f, indent=2)

        logger.info(f"Rolled back '{model_name}' from '{current_version}' to '{target_version}'.")
        return new_active_data

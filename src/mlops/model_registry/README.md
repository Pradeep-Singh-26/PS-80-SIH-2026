# Local File-Based Model Registry (Track B — Task 11)

Lightweight, production-grade filesystem model registry for regime-conditioned forecast bias correction and probabilistic uncertainty models.

---

## Architecture & Layout

```text
models/
└── <model_name>/
    ├── v001/
    │   ├── model.joblib      # Compressed serialized model artifact
    │   └── metadata.json     # Hyperparameters, metrics, feature schema & SHA-256 hash
    ├── v002/
    │   ├── model.joblib
    │   └── metadata.json
    └── active.json           # Currently active version pointer + rollback audit history
```

---

## Core Capabilities

1. **Deterministic Versioning**: Auto-incrementing tags (`v001`, `v002`, ...).
2. **Cryptographic Checksums**: SHA-256 integrity validation on every load.
3. **Feature Schema Validation**: Enforces exact 19-feature ordering and names prior to model instantiation.
4. **Active Version Management**: Pointer-based active version tracking (`active.json`).
5. **Zero-Data-Loss Rollback**: Safe rollback to previous operational versions without deleting artifacts.

---

## Example Usage

```python
from src.mlops.model_registry import ModelRegistry

registry = ModelRegistry(registry_root="models")

# 1. Register a newly trained model
registry.register_model(
    model_name="bias_corrector_ml",
    model_obj=trained_corrector_obj,
    model_type="HistGradientBoostingRegressor",
    feature_names=EXACT_ML_FEATURES,
    metrics={"mae": 19.46, "rmse": 25.45},
    data_status="synthetic_fixture",
    set_as_active=True,
)

# 2. Load active model with schema verification
model, metadata = registry.load_model(
    model_name="bias_corrector_ml",
    expected_features=EXACT_ML_FEATURES,
)

# 3. Rollback if needed
registry.rollback(model_name="bias_corrector_ml")
```

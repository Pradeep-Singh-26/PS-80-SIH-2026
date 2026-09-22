# PS-80 SIH 2026: Regime-Aware AI Post-Processing

This repository implements an AI-based post-processing system for monsoon rainfall forecasts. 

## Structure & Architecture
The system is divided into three functional tracks with strict file-contract boundaries.

- **Track A:** Data Ingest & Weather Regime Classification
- **Track B:** Bias Correction & Ensembling (ML/AI)
- **Track C:** Post-Processing, Verification, Alerts, and Serving (API & Dashboard)

## Getting Started

1. Set up your environment:
   ```bash
   pip install -r requirements.txt
   ```
2. Generate synthetic fixture data (to test without real NWP inputs):
   ```bash
   python tests/fixtures/generate_fixtures.py
   ```
3. Run the orchestration pipeline:
   ```bash
   python run_pipeline.py --config config.test.yaml
   ```

## Documentation

For full details, please refer to the `docs/` directory:
- [Architecture](docs/architecture.md)
- [API Reference](docs/api_reference.md)
- [User Guide](docs/user_guide.md)

# User Guide

This guide explains how to run and interact with the PS-80 Track C system.

## Setup and Development

### Running the Pipeline on Fixture Data
To verify the system without Track A/B real data, generate the synthetic test fixtures and run the pipeline:

```bash
# Generate fixture data
python tests/fixtures/generate_fixtures.py

# Run the full pipeline
python run_pipeline.py --config config.test.yaml
```

This will run the aggregation, verification, and alerting stages and populate the `outputs/` directory.

### Starting the API
The API serves the processed data. It reads from the `outputs/` directory based on paths defined in `config.yaml` (or `config.test.yaml`).

```bash
# Set environment variable for test data
export CONFIG_PATH=config.test.yaml  # Linux/Mac
$env:CONFIG_PATH="config.test.yaml"  # Windows PowerShell

# Start the server
uvicorn api.main:app --reload
```
You can view the interactive API docs at `http://localhost:8000/docs`.

### Starting the Dashboard
The Streamlit dashboard provides a visual interface over the data.

```bash
# With the API running, in a new terminal:
export CONFIG_PATH=config.test.yaml
streamlit run dashboard/web/app.py
```
Open the provided local URL (usually `http://localhost:8501`) in your browser.

## Running with Docker

You can spin up both the API and Dashboard simultaneously using Docker Compose:

```bash
cd infra/docker
docker-compose up --build
```
This automatically mounts the local `data/` and `outputs/` volumes so the dashboard reflects pipeline updates in real time.

## Customizing Alert Rules
Alert rules are defined in `src/alerts/alert_rules.yaml`. You can tweak the conditions (e.g. change `corrected_rainfall_min_mm` from `64.5` to `70`) without touching the python code. Rerun `python run_pipeline.py --stage alerts` to apply changes.

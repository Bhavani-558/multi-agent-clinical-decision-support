# CDSS: Multi-Agent Clinical Decision Support System

## 1. Project Name
**CDSS** (Multi-Agent Clinical Decision Support System)

## 2. Purpose of the CDSS
The Clinical Decision Support System (CDSS) is designed as a research-oriented, multi-agent platform that assists healthcare professionals by integrating data preprocessing, predictive modeling, knowledge graphs, evidence extraction, automated reasoning, decision fusion, and clinical reporting.

## 3. High-Level Architecture
The CDSS architecture comprises several specialized modules and agents working in tandem:
- **Agents Layer**: Specialized autonomous agents (`prediction_agent`, `evidence_agent`, `reasoning_agent`) handling task execution.
- **Knowledge & Evidence Layer**: Neo4j knowledge graph integration paired with evidence retrieval capabilities.
- **ML & Analytics Layer**: Prediction, explainability (SHAP), and model artifacts for domain-specific clinical predictions (e.g., diabetes, hypertension, heart disease).
- **Reasoning & Fusion Layer**: Logic synthesis combining quantitative models with clinical evidence and structured reasoning rules.
- **Application & Interface**: FastAPI / application layer and reporting modules for user interaction.

## 4. Directory Structure Overview
- `data/`: Contains raw data (`raw/`), preprocessed datasets (`processed/`), and code/id mappings (`mappings/`).
- `models/`: Trained machine learning models segregated by condition (`diabetes/`, `hypertension/`, `heart_disease/`, `other/`).
- `src/`: Core source packages covering preprocessing, prediction, explainability, knowledge graph, evidence, reasoning, fusion, and reporting.
- `agents/`: Autonomous agent definitions (`prediction_agent.py`, `evidence_agent.py`, `reasoning_agent.py`).
- `neo4j/`: Graph database schemas, Cypher queries, and data import scripts.
- `tests/`: Automated test suites for unit and integration testing.
- `configs/`: System, agent, and pipeline configuration files.
- `notebooks/`: Exploratory data analysis and research notebooks.
- `app/`: Application entrypoints and interface components.
- `evaluation/`: System benchmarking and evaluation scripts.

## 5. Important Disclaimer
> [!IMPORTANT]
> **Research & Decision-Support System Only**: This software is developed strictly for research and clinical decision-support purposes. It is **NOT** an autonomous clinical diagnosis system. Final medical decisions must always be made by qualified healthcare professionals.

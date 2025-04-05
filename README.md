# Entity Identifier

A Python-based project for identifying and processing trade finance entities using advanced language models and graph-based processing.

## Project Structure

```
.
├── src/               # Source code directory
├── notebooks/         # Jupyter notebooks for analysis and testing
├── bol/              # Bill of Lading related components
├── .langgraph_api/   # LangGraph API configurations
├── requirements.txt   # Python dependencies
├── pyproject.toml    # Project configuration and metadata
├── graph_2.py        # Graph processing implementation v2
└── graph_3.py        # Graph processing implementation v3
```

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure environment variables:
Create a `.env` file with necessary API keys and configurations.

## Features

- Entity identification and extraction from trade finance documents
- Graph-based processing for entity relationships
- Integration with language models for advanced text analysis
- Bill of Lading (BOL) document processing
- Jupyter notebooks for interactive analysis

## Development

The project uses:
- Python for core implementation
- LangGraph for graph-based processing
- Environment variables for configuration
- Jupyter notebooks for analysis and testing

## License

[License information to be added]

## Contributing

[Contribution guidelines to be added] 
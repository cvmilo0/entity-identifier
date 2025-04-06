# Trade Finance Analyst

OCR using QWEN2.5 VL for analyzing Trade Finance documents, especially focused on identifying and extracting entities from commercial documents such as Bills of Lading.

## Features

- Automatic identification of commercial entities in documents
- Processing of images and PDFs of Bills of Lading
- Analysis using AI agents with LangSmith and other services
- Graph-based system for information processing

## Project Structure

```
.
├── README.md
├── bol                         # Directory with Bills of Lading images
│   ├── billoflading.jpg        # Various document formats for processing
│   ├── billoflading.pdf
│   ├── billoflading_*.webp/png/jpg
│   └── maersk_bolivia.jpg
├── notebooks                   # Jupyter notebooks for development and analysis
│   ├── graph.ipynb
│   ├── qwen.ipynb
│   └── qwen.py
├── pyproject.toml              # Project configuration
├── requirements.txt            # Project dependencies
└── src                         # Main source code
    └── agent                   # AI agent components
        ├── graph.py            # Graph-based processing implementation
        ├── nodes.py            # Nodes for information processing
        ├── prompts.py          # Prompt templates for language models
        ├── state.py            # Agent state management
        └── utils.py            # General utilities
```

## Requirements

- Python 3.8+
- Access to vision and language APIs (configured through environment variables)

## Environment Setup

### Environment Variables

The project requires the following environment variables:

```env
VISION_AGENT_API_KEY=****
OPENROUTER_API_KEY=****
LANGSMITH_PROJECT=entity-identifier
LANGSMITH_API_KEY=****
DEEPSEEK_API_KEY=****
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/cvmilo0/tf_analyst.git
cd tf_analyst
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .  # Install the project in development mode
```

4. Configure environment variables:
   - Create a `.env` file in the project root
   - Add the necessary environment variables

## Usage

The project can be used in several ways:

1. **Using notebooks:**
   - Open and run the notebooks in `notebooks/` for interactive analysis

2. **As a library:**
   - Import components from the `src.agent` module to use in your own code

3. **Document processing:**
   - Use the system to analyze Bill of Lading documents
   - Extract important entities such as shippers, consignees, goods, etc.

## Contributing

Contributions are welcome. Please open an issue to discuss proposed changes.

## License

This project is private and its use is restricted. 
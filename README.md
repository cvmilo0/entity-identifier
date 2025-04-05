# Entity Identifier

Un proyecto que utiliza LangGraph para procesar y analizar documentos, identificando entidades, individuos y detalles relevantes.

## Características

- Procesamiento de documentos PDF e imágenes
- Identificación de entidades y partes intervinientes
- Análisis de detalles de carga y envío
- Sistema de retroalimentación humana
- Procesamiento paralelo de información

## Requisitos

- Python >= 3.9
- Dependencias listadas en requirements.txt

## Instalación

```bash
# Clonar el repositorio
git clone https://github.com/cvmilo0/entity_identifier.git
cd entity_identifier

# Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: .\venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## Configuración

Crea un archivo `.env` en la raíz del proyecto con las siguientes variables:

```env
DEEPSEEK_API_KEY=tu_api_key
OPENROUTER_API_KEY=tu_api_key
```

## Uso

El proyecto utiliza LangGraph para crear un flujo de trabajo que procesa documentos y extrae información relevante.

```python
from src.agent.graph import workflow

# Compilar el workflow
graph = workflow.compile()

# Ejecutar el workflow con un documento
result = graph.invoke({
    "file_path": "ruta/al/documento.pdf",
    "extraction_schema": schema_dict
})
```

## Estructura del Proyecto

```
entity_identifier/
├── src/
│   └── agent/
│       ├── __init__.py
│       ├── graph.py      # Definición del workflow
│       ├── state.py      # Estados y tipos
│       ├── prompts.py    # Prompts para LLMs
│       └── utils.py      # Funciones auxiliares
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Licencia

Este proyecto está bajo la Licencia MIT.
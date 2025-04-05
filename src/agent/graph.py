import base64
import json
from dotenv import load_dotenv
from os import getenv, path
import requests
import io
from src.agent.utils import process_json_response, format_interrupt_message
from src.agent.state import OverallState, OverallStateOutput, OverallStateInput
from src.agent.prompts import OCR_PROMPT, QUALITY_ASSURANCE_PROMPT
from langgraph.graph import StateGraph, START, END
from pdf2image import convert_from_path
from langchain_deepseek import ChatDeepSeek
from langchain_core.rate_limiters import InMemoryRateLimiter
from langgraph.types import interrupt, Command
from typing import Literal
from langgraph.checkpoint.memory import MemorySaver
from langgraph.constants import Send

load_dotenv()   

# Rate limiter configuration
rate_limiter = InMemoryRateLimiter(
    requests_per_second=4,
    check_every_n_seconds=0.1,
    max_bucket_size=10,
)

# LLM configuration
if not getenv('DEEPSEEK_API_KEY'):
    raise ValueError("DEEPSEEK_API_KEY must be set in environment variables")

llm = ChatDeepSeek(
    api_key=getenv('DEEPSEEK_API_KEY'),
    model="deepseek-chat",
    temperature=0,
    rate_limiter=rate_limiter
)

# define file encoder node
def encode_file_to_base64(state: OverallState):
    """
    Convert a file (pdf or image) to base64
    """
    extension = path.splitext(state.file_path)[1].lower()
    if extension == ".pdf":
        images = convert_from_path(state.file_path)
        if not images:
            raise Exception("No se pudo extraer ninguna imagen del PDF")
        img_byte_arr = io.BytesIO()
        images[0].save(img_byte_arr, format="PNG")
        return {"file_base64": base64.b64encode(img_byte_arr.getvalue()).decode("utf-8")}
    else:
        with open(state.file_path, "rb") as file:
            return {"file_base64": base64.b64encode(file.read()).decode("utf-8")}
        
#define document analyser node - API call
def analyze_document(state: OverallState):
    """
    Analyse a document making an OPENROUTER API call - Qwen2.5VL model
    """
    # encode file to base64
    file_base64 = state.file_base64
    
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {getenv('OPENROUTER_API_KEY')}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": "qwen/qwen2.5-vl-72b-instruct:free",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": OCR_PROMPT
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{file_base64}"
                            }
                        }
                    ]
                }
            ]
        })
    )

    result = response.json()
    parsed_result = process_json_response(result)
    
    # Extraer cada componente del resultado analizado
    return {
        "document": parsed_result["document"],
        "entities": parsed_result["entities"],
        "individuals": parsed_result["individuals"],
        "details": parsed_result["details"],
        "cargo": parsed_result["cargo"]
    }

# define quality assurance node
def review_quality(state: OverallState):
    """
    Analyse the quality of the document
    """
    # input variables
    document = state.document
    entities = state.entities
    individuals = state.individuals
    details = state.details
    cargo = state.cargo
    feedback_on_extraction = state.feedback_on_extraction        

    # llm structured output
    llm_structured_output = llm.with_structured_output(state.extraction_schema)

    # prompt
    query_instructions = QUALITY_ASSURANCE_PROMPT.format(
        document=document,
        entities=entities, 
        individuals=individuals, 
        details=details, 
        cargo=cargo,
        feedback_on_extraction=feedback_on_extraction
    )

    # llm call
    response = llm_structured_output.invoke([
        {"role": "system", "content": query_instructions},
        {
            "role": "user",
            "content": "Produce a structured output from these notes.",
        },
    ])

    return {
        "document": response["document"],
        "entities": response["entities"],
        "individuals": response["individuals"],
        "details": response["details"],
        "cargo": response["cargo"]
    }

def human_feedback(state: OverallState) -> Command[Literal["review_quality", END]]:
    """
    Get human feedback and route to next steps based on the response.
    
    This node:
    1. Formats the extracted information for human review
    2. Gets feedback via an interrupt
    3. Routes to either:
       - End of subgraph if extraction is approved
       - Quality analysis again if feedback is provided
    """
    # get data
    document_type = state.document.type
    document = state.document
    entities = state.entities
    individuals = state.individuals
    details = state.details
    cargo = state.cargo
    feedback_on_extraction = state.feedback_on_extraction

    # Usar la función de utilidad para formatear el mensaje
    interrupt_message = format_interrupt_message(
        document_type=document_type,
        document=document,
        entities=entities,
        individuals=individuals,
        details=details,
        cargo=cargo,
        feedback_on_extraction=feedback_on_extraction
    )
    
    feedback = interrupt(interrupt_message)

    # Si el usuario aprueba la extracción, finalizar el subgrafo
    if isinstance(feedback, bool) and feedback is True:
        # Terminamos el subgrafo y continuamos en el workflow principal
        return Command(goto=END)
    
    # Si el usuario proporciona feedback, volver a analizar la calidad
    elif isinstance(feedback, str):
        return Command(
            update={"feedback_on_extraction": feedback},
            goto="review_quality"
        )
    else:
        raise TypeError(f"Interrupt value of type {type(feedback)} is not supported.")

def proxy_node(state: OverallState):
    """
    Proxy node para distribuir a los nodos de procesamiento
    """
    # Devolvemos el estado tal cual para que se pueda distribuir a los nodos siguientes
    return state

def router(state: OverallState):
    nodes = ['format_entities', 'format_individuals', 'format_company']
    return nodes

def format_entities(state: OverallState):
    """
    Format entities - Nodo de prueba para procesamiento paralelo
    """
    entities = state.entities
    # Simplemente añadir un sufijo a los nombres de las entidades para mostrar que este nodo se ejecutó
    for entity in entities:
        entity.name = f"{entity.name} [PROCESADO POR FORMAT_ENTITIES]"
    
    return {"entities": entities, "entities_processed": True}

def format_individuals(state: OverallState):
    """
    Format individuals - Nodo de prueba para procesamiento paralelo
    """
    individuals = state.individuals
    # Añadir un sufijo a los nombres de los individuos
    for individual in individuals:
        individual.name = f"{individual.name} [PROCESADO POR FORMAT_INDIVIDUALS]"
    
    return {"individuals": individuals, "individuals_processed": True}

def format_company(state: OverallState):
    """
    Format company - Nodo de prueba para procesamiento paralelo
    """
    # Añadir información formateada sobre la compañía
    cargo = state.cargo
    if cargo:
        cargo.description = f"{cargo.description} [PROCESADO POR FORMAT_COMPANY]"
    
    return {"cargo": cargo, "company_processed": True}

subgraph = StateGraph(OverallState, input=OverallStateInput, output=OverallStateOutput)

# Add nodes
subgraph.add_node('encode_file', encode_file_to_base64)
subgraph.add_node('analyze_document', analyze_document)
subgraph.add_node('review_quality', review_quality)
subgraph.add_node('human_feedback', human_feedback)

# Add edges
subgraph.add_edge(START, 'encode_file')
subgraph.add_edge('encode_file', 'analyze_document')
subgraph.add_edge('analyze_document', 'review_quality')
subgraph.add_edge('review_quality', 'human_feedback')
subgraph.add_edge('human_feedback', END)

# Compilar el subgrafo
compiled_subgraph = subgraph.compile()

# Actualizar el workflow principal
workflow = StateGraph(OverallState, input=OverallStateInput, output=OverallStateOutput)

# Eliminar los nodos del subgrafo del workflow principal
workflow.add_node('format_entities', format_entities)
workflow.add_node('format_individuals', format_individuals)
workflow.add_node('format_company', format_company)
workflow.add_node('proxy_node', proxy_node)
# Crear un nuevo nodo en el workflow principal que ejecuta el subgraph compilado
workflow.add_node('document_processing', compiled_subgraph)

# Actualizar las conexiones
workflow.add_edge(START, 'document_processing')
workflow.add_edge('document_processing', 'proxy_node')
workflow.add_edge('proxy_node', 'format_entities')
workflow.add_edge('proxy_node', 'format_individuals') 
workflow.add_edge('proxy_node', 'format_company')
workflow.add_edge('format_entities', END)
workflow.add_edge('format_individuals', END)
workflow.add_edge('format_company', END)

graph = workflow.compile()
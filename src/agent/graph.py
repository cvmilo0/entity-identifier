from src.agent.state import OverallState, OverallStateOutput, OverallStateInput
from langgraph.graph import StateGraph, START, END
from src.agent.nodes import encode_file_to_base64, analyze_document, review_quality, human_feedback, format_entities, format_individuals, format_company, proxy_node


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
#subgraph.add_edge('human_feedback', END) - not required, human on the loop command

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
import json

# Auxiliary function to process the JSON response of the document analysis
def process_json_response(result):
    """
    Process the JSON response of the document analysis and extract the content.
    Returns the parsed content from OpenRouter API response.
    """
    # If result is already a dictionary, process it
    if isinstance(result, dict):
        try:
            # Estructura típica de la respuesta de OpenRouter API
            if 'choices' in result and len(result['choices']) > 0:
                message_content = result['choices'][0]['message']['content']
                
                # Si el contenido es una cadena JSON, intentamos analizarla
                if isinstance(message_content, str) and (message_content.startswith('{') or message_content.startswith('```')):
                    try:
                        # Eliminar formato markdown si existe
                        if message_content.startswith('```'):
                            clean_content = message_content.strip()
                            if clean_content.startswith('```json'):
                                clean_content = clean_content.replace('```json', '', 1)
                            if clean_content.endswith('```'):
                                clean_content = clean_content.replace('```', '', 1)
                            clean_content = clean_content.strip()
                            return json.loads(clean_content)
                        else:
                            return json.loads(message_content)
                    except json.JSONDecodeError:
                        # Si no podemos analizar como JSON, devolvemos el texto tal cual
                        return message_content
                else:
                    # Si no es una cadena o no parece JSON, devolvemos el contenido tal cual
                    return message_content
            
            # Si no encontramos choices, devolvemos el resultado completo
            return result
            
        except (KeyError, IndexError) as e:
            # En caso de error, proporcionamos información detallada
            print(f"Error al procesar la respuesta: {str(e)}")
            print(f"Estructura de la respuesta: {result}")
            return result

    # Si result es una cadena de texto, procesarla primero
    if isinstance(result, str):
        # Eliminar formato markdown si existe
        if result.startswith("```json"):
            result = result.replace("```json", "", 1)
        if result.endswith("```"):
            result = result.replace("```", "", 1)
                
        # Analizar JSON y procesar
        try:
            parsed_result = json.loads(result.strip())
            return process_json_response(parsed_result)  # Llamada recursiva con el diccionario analizado
        except json.JSONDecodeError:
            # Si no es JSON válido, devolver la cadena original
            return result
            
    # Si no es ni diccionario ni cadena, devolver tal cual
    return result

def format_interrupt_message(document_type: str, document: any, entities: list, individuals: list, details: any, cargo: any, feedback_on_extraction: str = None) -> str:
    """
    Formatea el mensaje de interrupción para la revisión del documento.
    
    Args:
        document_type: Tipo de documento
        document: Objeto documento con la información básica
        entities: Lista de entidades
        individuals: Lista de individuos
        details: Objeto con detalles del envío
        cargo: Objeto con detalles de la carga
        feedback_on_extraction: Feedback previo (opcional)
    
    Returns:
        str: Mensaje formateado para la interrupción
    """
    # Formatear entidades
    entities_str = "\n".join([
        f"📍 Entidad: {entity.name}\n"
        f"   📌 Dirección: {entity.address or 'No especificada'}\n"
        f"   🌍 País: {entity.country or 'No especificado'}\n"
        f"   📧 Email: {entity.email or 'No especificado'}\n"
        f"   📞 Teléfono: {entity.phone or 'No especificado'}\n"
        for entity in entities
    ])
    
    # Formatear individuos
    individuals_str = "\n".join([
        f"👤 Persona: {individual.name}\n"
        f"   🏢 Empresa: {individual.company or 'No especificada'}\n"
        f"   💼 Rol: {individual.role or 'No especificado'}\n"
        f"   🌍 País: {individual.country or 'No especificado'}\n"
        f"   📧 Email: {individual.email or 'No especificado'}\n"
        for individual in individuals
    ])

    # Formatear detalles del documento
    doc_details = [
        f"📄 Tipo: {document.type}",
        f"🔢 Número: {document.number}",
        f"📅 Fecha de emisión: {document.date_of_issue}",
        f"🚢 Fecha de embarque: {document.date_of_shipment}"
    ]

    # Formatear detalles del envío
    shipping_details = [
        f"📍 Lugar de recepción: {details.place_of_receipt}",
        f"🚢 Puerto de carga: {details.port_of_loading}",
        f"🏁 Puerto de descarga: {details.port_of_discharge}",
        f"⛴️ Nombre del buque: {details.vessel_name}",
        f"📍 Lugar de entrega: {details.place_of_delivery}",
        f"📦 Contenedor: {details.container}",
        f"⚖️ Peso bruto: {details.gross_weight}",
        f"📏 Medidas: {details.measurement}",
        f"💰 Flete: {details.freight}"
    ]

    # Formatear detalles de la carga
    cargo_details = [
        f"📦 Nombre del artículo: {cargo.item_name}",
        f"📝 Descripción: {cargo.description}",
        f"🔢 Cantidad: {cargo.quantity}",
        f"📋 Lista de empaque: {cargo.packing_list}",
        f"📜 Incoterm: {cargo.incoterm or 'No especificado'}",
        f"📝 Notas adicionales: {cargo.additional_notes}"
    ]

    # Crear separador visual
    separator = "\n" + "═" * 50 + "\n"

    # Construir mensaje
    return f"""
{'═' * 50}
🔍 REVISIÓN DE DOCUMENTO: {document_type.upper()}
{'═' * 50}

📄 INFORMACIÓN DEL DOCUMENTO:
{separator.join(doc_details)}

🏢 ENTIDADES:
{entities_str}

👥 INDIVIDUOS:
{individuals_str}

🚢 DETALLES DE ENVÍO:
{separator.join(shipping_details)}

📦 DETALLES DE LA CARGA:
{separator.join(cargo_details)}

💬 FEEDBACK PREVIO:
{feedback_on_extraction or 'No hay feedback previo'}

{'═' * 50}

❓ ¿La información extraída cumple con sus necesidades?

✅ Escriba 'true' para aprobar el documento.
✍️  O proporcione feedback para regenerar el documento:"""
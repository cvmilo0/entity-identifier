import base64
import json
import requests
from os import getenv, path
from dotenv import load_dotenv
from pdf2image import convert_from_path
import io
from PIL import Image
from entity_identifier.prompts import OCR_PROMPT

load_dotenv()

def encode_file_to_base64(file_path):
    """Convierte un archivo (PDF o imagen) a base64"""
    # Obtener la extensión del archivo
    extension = path.splitext(file_path)[1].lower()
    
    try:
        if extension == '.pdf':
            # Convertir PDF a imagen
            images = convert_from_path(file_path)
            if not images:
                raise Exception("No se pudo extraer ninguna imagen del PDF")
            
            # Usar la primera página
            img_byte_arr = io.BytesIO()
            images[0].save(img_byte_arr, format='PNG')
            img_byte_arr = img_byte_arr.getvalue()
            return base64.b64encode(img_byte_arr).decode('utf-8')
        else:
            # Para archivos de imagen
            with open(file_path, "rb") as file:
                return base64.b64encode(file.read()).decode('utf-8')
    except Exception as e:
        raise Exception(f"Error al codificar el archivo: {str(e)}")
    
def analizar_documento(ruta_archivo):
    """Analiza un documento (PDF o imagen) usando el modelo Qwen"""
    try:
        archivo_base64 = encode_file_to_base64(ruta_archivo)
        
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
                                    "url": f"data:image/jpeg;base64,{archivo_base64}"
                                }
                            }
                        ]
                    }
                ]
            })
        )
        
        resultado = response.json()
        
        # Manejar errores específicos de la API
        if 'error' in resultado:
            error_code = resultado['error'].get('code')
            error_message = resultado['error'].get('message')
            provider = resultado['error'].get('metadata', {}).get('provider_name', 'desconocido')
            
            if error_code == 429:
                return (f"Error: Demasiadas solicitudes al proveedor {provider}. "
                       "Por favor, espera unos minutos antes de intentar nuevamente.")
            else:
                return f"Error del proveedor {provider}: {error_message} (Código: {error_code})"
        
        # Si no hay error, procesar la respuesta normal
        if 'choices' in resultado:
            return resultado['choices'][0]['message']['content']
        else:
            print("Respuesta inesperada:")
            print(json.dumps(resultado, indent=2))
            return "Error: Formato de respuesta inesperado"
            
    except Exception as e:
        return f"Error al procesar el documento: {str(e)}"
    


def procesar_resultado_json(json_string):
    """
    Procesa el resultado JSON del análisis del documento y lo convierte en un diccionario Python.
    
    Args:
        json_string (str): String que contiene el JSON a procesar
        
    Returns:
        dict: Diccionario con la información procesada
    """
    try:
        # Eliminar los caracteres de formato markdown si están presentes
        if json_string.startswith("```json"):
            json_string = json_string.replace("```json", "", 1)
        if json_string.endswith("```"):
            json_string = json_string.replace("```", "", 1)
            
        # Limpiar espacios en blanco innecesarios
        json_string = json_string.strip()
        
        # Convertir el string a diccionario
        resultado = json.loads(json_string)
        
        return resultado
    except json.JSONDecodeError as e:
        raise Exception(f"Error al decodificar el JSON: {str(e)}")
    except Exception as e:
        raise Exception(f"Error inesperado al procesar el JSON: {str(e)}")

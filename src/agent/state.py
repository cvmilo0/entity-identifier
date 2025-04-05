from typing import List, Optional, Union, TypedDict
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from typing import Any


DEFAULT_EXTRACTION_SCHEMA = {
    "title": "DocumentAnalysis",
    "description": "Analyze and extract information from a trade finance document",
    "type": "object",
    "properties": {
        "document": {
            "type": "object",
            "description": "Basic document information",
            "properties": {
                "type": {"type": "string", "description": "Type of document (e.g., Bill of Lading)"},
                "number": {"type": "string", "description": "Document identification number"},
                "date_of_issue": {"type": "string", "description": "Date when the document was issued"},
                "date_of_shipment": {"type": "string", "description": "Date of cargo shipment"}
            },
            "required": ["type", "number", "date_of_issue", "date_of_shipment"]
        },
        "entities": {
            "type": "array",
            "description": "List of commercial entities involved in the transaction",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Entity name"},
                    "role": {"type": "string", "description": "Role in the transaction"},
                    "address": {"type": "string", "description": "Physical address"},
                    "city": {"type": "string", "description": "City"},
                    "country": {"type": "string", "description": "Country"},
                    "postal_code": {"type": "string", "description": "Postal code"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "email": {"type": "string", "description": "Email address"}
                },
                "required": ["name", "role"]
            }
        },
        "individuals": {
            "type": "array",
            "description": "List of individuals involved in the transaction",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Individual's name"},
                    "company": {"type": "string", "description": "Associated company"},
                    "role": {"type": "string", "description": "Role in the transaction"},
                    "country": {"type": "string", "description": "Country"},
                    "email": {"type": "string", "description": "Email address"}
                },
                "required": ["company", "role"]
            }
        },
        "details": {
            "type": "object",
            "description": "Shipment details",
            "properties": {
                "place_of_receipt": {"type": "string", "description": "Initial receipt location"},
                "port_of_loading": {"type": "string", "description": "Loading port"},
                "port_of_discharge": {"type": "string", "description": "Discharge port"},
                "vessel_name": {"type": "string", "description": "Vessel name"},
                "place_of_delivery": {"type": "string", "description": "Final delivery location"},
                "container": {"type": "string", "description": "Container number"},
                "gross_weight": {"type": "string", "description": "Gross weight"},
                "measurement": {"type": "string", "description": "Cargo measurements"},
                "freight": {"type": "string", "description": "Freight cost"}
            },
            "required": ["port_of_loading", "port_of_discharge", "vessel_name"]
        },
        "cargo": {
            "type": "object",
            "description": "Cargo information",
            "properties": {
                "item_name": {"type": "string", "description": "Name of the product"},
                "description": {"type": "string", "description": "Detailed cargo description"},
                "quantity": {"type": "string", "description": "Quantity of units"},
                "packing_list": {"type": "string", "description": "Packaging details"},
                "incoterm": {"type": "string", "description": "International trade term"},
                "additional_notes": {"type": "string", "description": "Additional information"}
            },
            "required": ["item_name", "description", "quantity"]
        }
    },
    "required": ["document", "entities", "details", "cargo"]
}

class DocumentInfo(BaseModel):
    """Document information"""
    type: Optional[str] = Field(description="document type (ej: Bill of Lading, Invoice, etc)")
    number: Optional[str] = Field(description="unique document identification number")
    date_of_issue: Optional[str] = Field(description="date of issue of the document")
    date_of_shipment: Optional[str] = Field(description="date of shipment of the cargo")

class Entity(BaseModel):
    """Entity information"""
    name: Optional[str] = Field(description="full name of the entity")
    role: Optional[str] = Field(description="role in the transaction (ej: Shipper, Consignee, etc)")
    address: Optional[str] = Field(description="full physical address")
    city: Optional[str] = Field(description="city of location")
    country: Optional[str] = Field(description="country of location")
    postal_code: Optional[str] = Field(description="postal code")
    phone: Optional[str] = Field(description="phone number")
    email: Optional[str] = Field(description="email")

class Individual(BaseModel):
    """Individual information"""
    name: Optional[str] = Field(description="full name of the individual")
    company: Optional[str] = Field(description="company to which the individual belongs")
    role: Optional[str] = Field(description="role of the individual in the transaction")
    country: Optional[str] = Field(description="country of origin/location")
    email: Optional[str] = Field(description="email")

class Details(BaseModel):
    """Shipment details"""
    place_of_receipt: Optional[str] = Field(description="place where the cargo is initially received")
    port_of_loading: Optional[str] = Field(description="loading port")
    port_of_discharge: Optional[str] = Field(description="discharge port")
    vessel_name: Optional[str] = Field(description="vessel name")
    place_of_delivery: Optional[str] = Field(description="final delivery place")
    container: Optional[str] = Field(description="container number")
    gross_weight: Optional[str] = Field(description="gross weight of the cargo")
    measurement: Optional[str] = Field(description="measurements/volume of the cargo")
    freight: Optional[str] = Field(description="freight cost")

class Cargo(BaseModel):
    """Cargo information"""
    item_name: Optional[str] = Field(description="name of the product or cargo")
    description: Optional[str] = Field(description="detailed description of the cargo")
    quantity: Optional[str] = Field(description="quantity of units")
    packing_list: Optional[str] = Field(description="details of the packaging and distribution")
    incoterm: Optional[str] = Field(description="international trade term applied")
    additional_notes: Optional[str] = Field(description="additional notes about the cargo")

class OverallStateInput(BaseModel):
    """Input state"""
    file_path: Optional[str] = Field(description="path to the file to be analyzed")

class OverallState(BaseModel):
    """Overall state during processing"""
    file_path: str = Field(description="path to the file being processed")
    file_base64: Optional[str] = Field(None, description="content of the file encoded in base64")
    document: Optional[DocumentInfo] = Field(None, description="document information")
    entities: Optional[List[Entity]] = Field(None, description="list of commercial entities involved")
    individuals: Optional[List[Individual]] = Field(None, description="list of individuals involved")
    details: Optional[Details] = Field(None, description="details of the shipment")
    cargo: Optional[Cargo] = Field(None, description="cargo information")
    extraction_schema: dict = Field(default=DEFAULT_EXTRACTION_SCHEMA, description="schema for extraction")
    feedback_on_extraction: Optional[Union[bool, str]] = Field(None, description="feedback on the extraction")

class OverallStateOutput(BaseModel):
    """Output state"""
    document: DocumentInfo = Field(description="information extracted from the document")
    entities: List[Entity] = Field(description="commercial entities identified")
    individuals: List[Individual] = Field(description="individuals identified")
    details: Details = Field(description="extracted shipment details")
    cargo: Cargo = Field(description="identified cargo information")
    
class SendState(TypedDict):
    entities: List[Entity]
    individuals: List[Individual]
    cargo: Cargo
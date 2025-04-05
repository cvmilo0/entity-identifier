OCR_PROMPT = """"Analyze this Bill of Lading image and return the information in the following JSON format. 
Make sure to:

1. Keep exactly the same structure
2. Fill in all possible fields
3. If a field is not present in the image, leave it as an empty string (""), do not invent information
4. Use DD/MM/YYYYYY date format when possible
5. Include units in numeric fields (example: "gross_weight": "1650 Kg")
6. Simplify the item_name
7. IMPORTANT: Include ALL commercial entities mentioned in the document, including:
 - Shipping company (carrier)
 - Customs brokers
 - Issuing companies
 - Any other company mentioned
 8. For each entity, specify its exact role in the document, make sure entities and individuals are correctly categorized.
{
    "document": {
        "type": "Bill of Lading",
        "number": "",
        "date_of_issue": "",
        "date_of_shipment": ""
    },
    "entities": [
        {
            "name": "",
            "role": "",
            "address": "",
            "city": "",
            "country": "",
            "postal_code": "",
            "phone": "",
            "email": ""
        }
    ],
    "individuals": [
        {
            "name": "",
            "company": "",
            "role": "",
            "country": "",
            "email": ""
        }
    ],
    "details": {
        "place_of_receipt": "",
        "port_of_loading": "",
        "port_of_discharge": "",
        "vessel_name": "",
        "place_of_delivery": "",
        "container": "",
        "gross_weight": "",
        "measurement": "",
        "freight": ""
    },
    "cargo": {
        "item_name": "",
        "description": "",
        "quantity": "",
        "packing_list": "",
        "incoterm": "",
        "additional_notes": ""
    }
}"""


QUALITY_ASSURANCE_PROMPT = """
You are a quality assurance expert tasked with reviewing the correct categorization of different data extracted from a document.

The data extracted from the document is the following:

<document>
{document}
</document>

<entities>
{entities}
</entities>

<individuals>
{individuals}
</individuals>

<details>
{details}
</details>

<cargo>
{cargo}
</cargo>

Your task is:
1. Review the data extracted from the document and ensure that individuals and entities are correctly categorized, if not, correct the categorization.
2. Make sure that data has no errors or inconsistencies.
3. Complete country names when possible.
4. Do not consider prefixes as a name, only use the name of the individual.

Additionally, please consider the following comments:
{feedback_on_extraction}

"""
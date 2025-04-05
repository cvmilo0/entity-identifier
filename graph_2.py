import asyncio
from typing import cast, Any, Literal
import json
import os
from dotenv import load_dotenv
import requests
from datetime import datetime


from tavily import AsyncTavilyClient
from langchain_core.rate_limiters import InMemoryRateLimiter
from langchain_core.runnables import RunnableConfig
from langgraph.graph import START, END, StateGraph
from pydantic import BaseModel, Field
from langchain_deepseek import ChatDeepSeek

from src.agent.configuration import Configuration
from src.agent.state import InputState, OutputState, OverallState
from src.agent.utils import deduplicate_and_format_sources, format_all_notes, format_linkedin_profile_detailed
from src.agent.prompts import (
    EXTRACTION_PROMPT,
    REFLECTION_PROMPT,
    INFO_PROMPT,
    QUERY_WRITER_PROMPT,
    LINKEDIN_INFO_PROMPT,
)

# Load environment variables
load_dotenv()

# Verify that the API keys are available
if not os.getenv("TAVILY_API_KEY"):
    raise ValueError("TAVILY_API_KEY is not configured in the environment variables")
if not os.getenv("DEEPSEEK_API_KEY"):
    raise ValueError("DEEPSEEK_API_KEY is not configured in the environment variables")
if not os.getenv("RAPIDAPI_KEY"):
    raise ValueError("RAPIDAPI_KEY is not configured in the environment variables")


# LLMs

rate_limiter = InMemoryRateLimiter(
    requests_per_second=4,
    check_every_n_seconds=0.1,
    max_bucket_size=10,  # Controls the maximum burst size.
)
deepseek_llm = ChatDeepSeek(
    model="deepseek-chat", temperature=0, rate_limiter=rate_limiter
)

# Search

tavily_async_client = AsyncTavilyClient()

class Queries(BaseModel):
    queries: list[str] = Field(
        description="List of search queries.",
    )

class ReflectionOutput(BaseModel):
    is_satisfactory: bool = Field(
        description="True if all required fields are well populated, False otherwise"
    )
    missing_fields: list[str] = Field(
        description="List of field names that are missing or incomplete"
    )
    search_queries: list[str] = Field(
        description="If is_satisfactory is False, provide 1-3 targeted search queries to find the missing information"
    )
    reasoning: str = Field(description="Brief explanation of the assessment")

# Nodes definitions

# LinkedIn search
async def research_linkedin(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Execute a LinkedIn profile search using RapidAPI.
    
    This function performs the following steps:
    1. Constructs a search query based on the person's information
    2. Makes a request to the LinkedIn Profile Data API
    3. Processes each profile individually
    4. Returns a list of formatted results, one per profile
    """
    
    url = "https://fresh-linkedin-profile-data.p.rapidapi.com/google-full-profiles"
    
    # Construct payload from person information
    payload = {
        "name": state.person.get("name", ""),
        "company_name": state.person.get("company", ""),
        "job_title": state.person.get("role", ""),
        "location": state.person.get("country", ""),
        "limit": Configuration.max_linkedin_profiles
    }
    
    headers = {
        "x-rapidapi-key": os.getenv("RAPIDAPI_KEY"),
        "x-rapidapi-host": "fresh-linkedin-profile-data.p.rapidapi.com",
        "Content-Type": "application/json"
    }


    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    linkedin_data = response.json()

    
    completed_notes = []

    # Process each profile individually
    if linkedin_data.get("data"):
        for profile in linkedin_data["data"]:
            # Create individual profile data
            formatted_profile = format_linkedin_profile_detailed({"data": [profile]})
            
            # Generate structured notes for this specific profile
            p = LINKEDIN_INFO_PROMPT.format(
                info=json.dumps(state.extraction_schema, indent=2),
                content=formatted_profile,
                people=state.person,
                user_notes=state.user_notes,
                date=datetime.now().strftime("%Y-%m-%d")
            )

            result = await deepseek_llm.ainvoke(p)
            completed_notes.append(str(result.content))

    # Return all profile notes
    return {"completed_linkedin_notes": completed_notes}


# Query generation
def generate_queries(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Generate search queries based on the user input and extraction schema."""
    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_search_queries = configurable.max_search_queries

    # Generate search queries
    structured_llm = deepseek_llm.with_structured_output(Queries)

    # Format system instructions
    person_str = f"name: {state.person['name']}"
    if "email" in state.person:
        person_str += f" email: {state.person['email']}"
    if "country" in state.person:
        person_str += f" country: {state.person['country']}"
    if "linkedin" in state.person:
        person_str += f" LinkedIn URL: {state.person['linkedin']}"
    if "role" in state.person:
        person_str += f" Role: {state.person['role']}"
    if "company" in state.person:
        person_str += f" Company: {state.person['company']}"

    query_instructions = QUERY_WRITER_PROMPT.format(
        person=person_str,
        info=json.dumps(state.extraction_schema, indent=2),
        user_notes=state.user_notes,
        max_search_queries=max_search_queries,
    )

    # Generate queries
    results = cast(
        Queries,
        structured_llm.invoke(
            [
                {"role": "system", "content": query_instructions},
                {
                    "role": "user",
                    "content": "Please generate a list of search queries related to the schema that you want to populate.",
                },
            ]
        ),
    )

    # Queries
    query_list = [query for query in results.queries]
    return {"search_queries": query_list}


# Web search
async def research_person(state: OverallState, config: RunnableConfig) -> dict[str, Any]:
    """Execute a multi-step web search and information extraction process.

    This function performs the following steps:
    1. Executes concurrent web searches using the Tavily API
    2. Deduplicates and formats the search results
    """

    # Get configuration
    configurable = Configuration.from_runnable_config(config)
    max_search_results = configurable.max_search_results

    # Web search
    search_tasks = []
    for query in state.search_queries:
        search_tasks.append(
            tavily_async_client.search(
                query,
                days=360,
                max_results=max_search_results,
                include_raw_content=True,
                topic="general",
            )
        )

    # Execute all searches concurrently
    search_docs = await asyncio.gather(*search_tasks)

    # Deduplicate and format sources
    source_str = deduplicate_and_format_sources(
        search_docs, max_tokens_per_source=1000, include_raw_content=True
    )
    # Generate structured notes relevant to the extraction schema
    p = INFO_PROMPT.format(
        info=json.dumps(state.extraction_schema, indent=2),
        content=source_str,
        people=state.person,
        user_notes=state.user_notes,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    # Invoke the LLM
    result = await deepseek_llm.ainvoke(p)
    # Add the LinkedIn data to the completed notes state
    return {"completed_web_notes": [str(result.content)]}


# Schema extraction
def gather_linkedin_notes_extract_schema(state: OverallState) -> dict[str, Any]:
    """Gather notes from the web search and extract the schema fields for each profile."""
    
    structured_llm = deepseek_llm.with_structured_output(state.extraction_schema)
    extracted_info_list = []

    # Process each set of notes individually
    for note in state.completed_linkedin_notes:
        # Extract schema fields for this profile
        system_prompt = EXTRACTION_PROMPT.format(
            info=json.dumps(state.extraction_schema, indent=2),
            notes=note,  # Use only the notes for this profile
            date=datetime.now().strftime("%Y-%m-%d")
        )
        
        result = structured_llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": "Produce a structured output from these notes.",
                },
            ]
        )
        extracted_info_list.append(result)

    # Return list of extracted information for each profile
    return {"info": extracted_info_list}

def gather_web_notes_extract_schema(state: OverallState) -> dict[str, Any]:
    """Gather notes from the web search and extract the schema fields."""

    # Format all notes
    notes = format_all_notes(state.completed_web_notes)

    # Extract schema fields
    system_prompt = EXTRACTION_PROMPT.format(
        info=json.dumps(state.extraction_schema, indent=2), 
        notes=notes,
        date=datetime.now().strftime("%Y-%m-%d")
    )
    structured_llm = deepseek_llm.with_structured_output(state.extraction_schema)
    result = structured_llm.invoke(
        [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Produce a structured output from these notes.",
            },
        ]
    )
    return {"info": [result]}    

# Reflection
def reflection(state: OverallState) -> dict[str, Any]:
    """Reflect on the extracted information and generate search queries to find missing information."""
    structured_llm = deepseek_llm.with_structured_output(ReflectionOutput)

    # Format reflection prompt
    system_prompt = REFLECTION_PROMPT.format(
        schema=json.dumps(state.extraction_schema, indent=2),
        info=state.info,
    )

    # Invoke
    result = cast(
        ReflectionOutput,
        structured_llm.invoke(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": "Produce a structured reflection output."},
            ]
        ),
    )

    if result.is_satisfactory:
        return {"is_satisfactory": result.is_satisfactory}
    else:
        return {
            "is_satisfactory": result.is_satisfactory,
            "search_queries": result.search_queries,
            "reflection_steps_taken": state.reflection_steps_taken + 1,
        }


# Route from reflection
def route_from_reflection(
    state: OverallState, config: RunnableConfig
) -> Literal[END, "research_person"]:  # type: ignore
    """Route the graph based on the reflection output."""
    # Get configuration
    configurable = Configuration.from_runnable_config(config)

    # If we have satisfactory results, end the process
    if state.is_satisfactory:
        return END

    # If results aren't satisfactory but we haven't hit max steps, continue research
    if state.reflection_steps_taken <= configurable.max_reflection_steps:
        return "research_person"

    # If we've exceeded max steps, end even if not satisfactory
    return END


# Graph

# Add nodes and edges
builder = StateGraph(
    OverallState,
    input=InputState,
    output=OutputState,
    config_schema=Configuration,
)
builder.add_node("gather_linkedin_notes_extract_schema", gather_linkedin_notes_extract_schema)
builder.add_node("gather_web_notes_extract_schema", gather_web_notes_extract_schema)
builder.add_node("generate_queries", generate_queries)
builder.add_node("research_person", research_person)
builder.add_node("research_linkedin", research_linkedin)
builder.add_node("reflection", reflection)

builder.add_edge(START, "generate_queries")
builder.add_edge(START, "research_linkedin")
builder.add_edge("generate_queries", "research_person")
builder.add_edge("research_linkedin", "gather_linkedin_notes_extract_schema")
builder.add_edge("research_person", "gather_web_notes_extract_schema")
builder.add_edge("gather_linkedin_notes_extract_schema", END)
builder.add_edge("gather_web_notes_extract_schema", "reflection")
builder.add_conditional_edges("reflection", route_from_reflection)

# Compile
graph = builder.compile()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os
from src.graph.workflow import app_graph
from src.utils.schema_inspector import parse_ddl_and_generate_snapshot

app = FastAPI(title="Ledger-Guard API")

class QueryRequest(BaseModel):
    user_query: str
    schema_ddl: Optional[str] = None # Optional if we have a stored schema, but for now passing it is easiest

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    audit_feedback: Optional[str]

# Global schema cache for simplicity
CURRENT_SCHEMA = {}

@app.get("/")
async def root():
    return {"message": "Ledger-Guard System Operational"}

@app.post("/schema")
async def update_schema(ddl: str):
    """
    Endpoint to update the context schema from specific DDL.
    """
    global CURRENT_SCHEMA
    if not ddl:
        raise HTTPException(status_code=400, detail="DDL content required")
    
    snapshot = parse_ddl_and_generate_snapshot(ddl)
    CURRENT_SCHEMA = snapshot
    return {"message": "Schema updated", "snapshot": snapshot}

@app.post("/query")
async def run_query(request: QueryRequest):
    """
    Main endpoint to process natural language to SQL execution.
    """
    if not CURRENT_SCHEMA and not request.schema_ddl:
        raise HTTPException(status_code=400, detail="Schema not defined. Please upload schema DDL first or include in request.")
    
    # If DDL is provided in request, update/use it temporarily
    schema_to_use = CURRENT_SCHEMA
    if request.schema_ddl:
        schema_to_use = parse_ddl_and_generate_snapshot(request.schema_ddl)
        
    initial_state = {
        "user_query": request.user_query,
        "schema_json": schema_to_use,
        "current_sql": None,
        "feedback": None,
        "execution_results": [],
        "iteration_count": 0
    }
    
    # Run the graph
    final_state = await app_graph.invoke(initial_state)
    
    # Check if we ended with feedback (meaning it failed max iterations or similar, though our graph loops infinitely currently without a max limit check in conditional edge)
    # Ideally we should add a max_limit to the conditional edge, but for this MVP script:
    
    return {
        "sql_query": final_state.get("current_sql"),
        "results": final_state.get("execution_results") or [],
        "audit_feedback": final_state.get("feedback")
    }

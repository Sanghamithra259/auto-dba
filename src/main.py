from dotenv import load_dotenv
load_dotenv()  # This injects the variables from .env into os.environ

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import os

# 1. Imports from your custom graph pipeline
from src.graph.workflow import app_graph
from src.utils.schema_inspector import parse_ddl_and_generate_snapshot

# 2. Define the Pydantic models first
class QueryRequest(BaseModel):
    user_query: str
    schema_ddl: Optional[str] = None 

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    audit_feedback: Optional[str]

# 3. Initialize the FastAPI application instance
app = FastAPI(title="Ledger-Guard API")

# 4. Initialize global schema cache
CURRENT_SCHEMA = {}

# 5. Define your application route endpoints
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

@app.post("/query", response_model=QueryResponse)
async def run_query(request: QueryRequest):
    """
    Main endpoint to process natural language to SQL execution.
    """
    if not CURRENT_SCHEMA and not request.schema_ddl:
        raise HTTPException(
            status_code=400, 
            detail="Schema metadata is completely missing. Please upload schema DDL first."
        )
        
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
    
    try:
        # FIXED: Removed 'await' since the graph runs on synchronous node functions
        final_state = app_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph Execution Runtime Failed: {str(e)}")
    
    sql_generated = final_state.get("current_sql")
    feedback_state = final_state.get("feedback")
    
    if feedback_state and not final_state.get("execution_results"):
        return {
            "sql_query": sql_generated or "Execution unfulfilled.",
            "results": [],
            "audit_feedback": f"Pipeline halted without execution: {feedback_state}"
        }
        
    return {
        "sql_query": sql_generated,
        "results": final_state.get("execution_results") or [],
        "audit_feedback": feedback_state
    }
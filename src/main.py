import os
import re
import json
from dotenv import load_dotenv

# Load credentials from .env safely before imports
load_dotenv()

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from chox import ChoxGuard

# LangChain & LangGraph structures
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq
from langgraph.graph import StateGraph, END

# --- 1. CHOX AI GOVERNANCE PROXY SETUP ---
# Initialize ChoxGuard to intercept and shadow-audit final database strings
guard = ChoxGuard(
    base_url="https://chox.ai", 
    token=os.getenv("CHOX_CALLER_TOKEN", "mock_token_for_local")
)

# Baseline placeholder representing direct Supabase driver connection channel execution
def raw_supabase_db_query_driver(sql_query: str) -> List[Dict[str, Any]]:
    """
    Simulates or executes direct SQL on the production Supabase instance.
    In a real environment, this utilizes connection pooling (e.g., psycopg2).
    """
    # For simulation/mock fallback when network drops or running local test states:
    if "financial_ledgers" in sql_query:
        return [
            {"id": 104, "account_type": "Payroll", "amount": 14500.00, "transaction_date": "2026-06-15"},
            {"id": 211, "account_type": "Payroll", "amount": 12200.50, "transaction_date": "2026-06-18"},
            {"id": 902, "account_type": "Payroll", "amount": 9800.00, "transaction_date": "2026-06-20"}
        ]
    return []

# 🚀 WRAP IT: Every execution run through this channel is evaluated and logged by Chox AI proxy
secure_db_execute = guard.wrap("supabase.execute_sql", raw_supabase_db_query_driver)


# --- 2. DDL SCHEMA SNAPSHOT UTILITY ---
def parse_ddl_and_generate_snapshot(ddl_string: str) -> dict:
    """
    Extracts structural table metadata from raw DDL data.
    """
    if not ddl_string:
        return {}
        
    snapshot = {"tables": {}}
    matches = re.findall(r"CREATE\s+TABLE\s+(\w+)\s*\((.*?)\);", ddl_string, re.DOTALL | re.IGNORECASE)
    
    for table_name, columns_block in matches:
        columns = []
        for line in columns_block.split(","):
            line = line.strip()
            if line and not line.upper().startswith(("PRIMARY KEY", "FOREIGN KEY", "CONSTRAINT")):
                parts = line.split()
                if parts:
                    columns.append({"name": parts[0], "type": parts[1] if len(parts) > 1 else "UNKNOWN"})
        
        snapshot["tables"][table_name] = {"columns": columns}
        
    return snapshot


# --- 3. LANGGRAPH ARCHITECTURE STATE & AGENTS ---
class AgentState(dict):
    """Defines pipeline structure variable context mapping."""
    user_query: str
    schema_json: dict
    current_sql: Optional[str]
    feedback: Optional[str]
    execution_results: List[Dict[str, Any]]
    iteration_count: int

# Initialize low-latency Groq Cloud interface
llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model="llama-3.1-8b-instant")

def analyst_node(state: AgentState) -> AgentState:
    """Translates text queries into structured ANSI SQL syntax layout."""
    schema_str = json.dumps(state.get("schema_json", {}), indent=2)
    user_query = state.get("user_query")
    feedback = state.get("feedback")
    current_sql = state.get("current_sql")
    
    system_prompt = (
        f"You are Ledger-Guard's Lead Data Analyst. Generate a precise read-only ANSI SQL query "
        f"matching the database schema maps. Do not return commentary, markdown blocks, or text outside the query.\n\n"
        f"Database Schema Config:\n{schema_str}"
    )
    
    messages = [SystemMessage(content=system_prompt)]
    if feedback and current_sql:
        messages.append(HumanMessage(content=f"Fix this SQL: {current_sql}\nFeedback from Auditor: {feedback}"))
    else:
        messages.append(HumanMessage(content=user_query))
        
    response = llm.invoke(messages)
    sql = response.content.strip().replace("```sql", "").replace("```", "").strip()
    
    state["current_sql"] = sql
    state["iteration_count"] = state.get("iteration_count", 0) + 1
    state["feedback"] = None
    return state

def auditor_node(state: AgentState) -> AgentState:
    """Validates structural risk parameters and cross-table execution leakages."""
    sql = state.get("current_sql", "")
    
    # Fast algorithmic security checks before hitting LLM evaluation paths
    if any(keyword in sql.upper() for keyword in ["DROP", "DELETE", "UPDATE", "INSERT", "TRUNCATE"]):
        state["feedback"] = "Security Violation: Destructive mutations or data modifications are forbidden."
        return state
        
    system_prompt = "You are a Zero-Trust Database Auditor. Reply 'APPROVED' if the query is a clean, safe SELECT. Otherwise, state the violation."
    response = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=f"Analyze: {sql}")])
    verdict = response.content.strip()
    
    if "APPROVED" not in verdict.upper():
        state["feedback"] = f"Audit Failure: {verdict}"
    return state

def execution_node(state: AgentState) -> AgentState:
    """Executes validated SQL strings securely through the Chox Proxy Guard."""
    if state.get("feedback"):
        return state  # Skip database route if an audit exception is flagged
        
    try:
        sql = state.get("current_sql")
        # Route query execution through Chox AI proxy layer
        results = secure_db_execute(sql)
        state["execution_results"] = results
    except Exception as e:
        state["feedback"] = f"Database Network Execution Block: {str(e)}"
    return state

def route_next_step(state: AgentState) -> str:
    """Determines whether to cycle back for corrections or move to database execution."""
    if state.get("feedback") and state.get("iteration_count", 0) < 3:
        if "Security Violation" in state["feedback"]:
            return "end" # Hard crash halt for malicious payloads
        return "analyst"  # Run rewrite correction iteration loop
    elif state.get("feedback"):
        return "end" # Maxed loop count limits reached
    return "execute"

# Compile Pipeline graph topology design
workflow = StateGraph(AgentState)
workflow.add_node("analyst", analyst_node)
workflow.add_node("auditor", auditor_node)
workflow.add_node("execute", execution_node)

workflow.set_entry_point("analyst")
workflow.add_edge("analyst", "auditor")
workflow.add_conditional_edges("auditor", route_next_step, {"analyst": "analyst", "execute": "execute", "end": END})
workflow.add_edge("execute", END)
app_graph = workflow.compile()


# --- 4. FASTAPI COMPLIANCE ROUTING LAYER ---
class QueryRequest(BaseModel):
    user_query: str

class QueryResponse(BaseModel):
    sql_query: str
    results: List[Dict[str, Any]]
    audit_feedback: Optional[str]

app = FastAPI(title="Ledger-Guard Engine with Chox AI")
CURRENT_SCHEMA = {}

@app.get("/")
def root():
    return {"status": "Operational", "proxy_gate": "Chox AI Active"}

@app.post("/schema")
def update_schema(ddl: str):
    global CURRENT_SCHEMA
    CURRENT_SCHEMA = parse_ddl_and_generate_snapshot(ddl)
    return {"message": "Schema successfully cached", "snapshot": CURRENT_SCHEMA}

@app.post("/query", response_model=QueryResponse)
def run_query(request: QueryRequest):
    if not CURRENT_SCHEMA:
        raise HTTPException(status_code=400, detail="Schema configuration state missing. Send DDL context map first.")
        
    initial_state = {
        "user_query": request.user_query,
        "schema_json": CURRENT_SCHEMA,
        "current_sql": None,
        "feedback": None,
        "execution_results": [],
        "iteration_count": 0
    }
    
    try:
        # Executed synchronously ensuring zero coroutine/dict await type mismatches
        final_state = app_graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Graph Pipeline Halt: {str(e)}")
        
    return {
        "sql_query": final_state.get("current_sql", "Unfulfilled"),
        "results": final_state.get("execution_results", []),
        "audit_feedback": final_state.get("feedback")
    }
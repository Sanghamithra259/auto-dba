# src/graph/executor.py
import psycopg2
import psycopg2.extras
import os
from src.graph.state import AgentState

def execution_node(state: AgentState) -> AgentState:
    sql_query = state.get("current_sql")
    if not sql_query:
        return {"execution_results": [], "feedback": "No SQL code received for execution."}

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return {"execution_results": [], "feedback": "Configuration Error: DATABASE_URL missing."}

    # CRITICAL LAST LINE OF DEFENSE: Guard against unsafe verbs programmatically
    # even if the LLM auditor accidentally approves it.
    disallowed_actions = ["DROP", "TRUNCATE", "ALTER", "DELETE FROM"]
    if any(action in sql_query.upper() for action in disallowed_actions):
        return {
            "execution_results": [], 
            "feedback": "Execution Blocked: Destructive mutations prohibited at the runtime driver boundary."
        }

    results = []
    conn = None
    try:
        conn = psycopg2.connect(db_url)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql_query)
            if cur.description:
                results = cur.fetchall()
            conn.commit()
            
        return {"execution_results": [dict(row) for row in results], "feedback": None}
        
    except Exception as e:
        if conn:
            conn.rollback() # Ensure transaction state resets safely on errors
        return {"feedback": f"Database Execution Error: {str(e)}", "execution_results": None}
    finally:
        if conn:
            conn.close()
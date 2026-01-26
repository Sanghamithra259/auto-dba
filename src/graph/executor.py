import psycopg2
import psycopg2.extras
import os
from src.graph.state import AgentState

def execution_node(state: AgentState) -> AgentState:
    """
    Executes the validated SQL query against Supabase.
    """
    sql_query = state.get("current_sql")
    if not sql_query:
        return {"execution_results": [], "feedback": "No SQL to execute."}

    # Connect to Supabase (Postgres)
    # Using psycopg2 for direct connection
    # Connection string format: postgres -> postgres://user:password@host:port/dbname
    # Supabase provides these details in Settings -> Database
    
    # We will look for a DATABASE_URL env var, or construct from individual vars
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        # Fallback to constructing it if individual vars exist (not standard in this setup but good practice)
        # Assuming DATABASE_URL is provided in .env
        return {"execution_results": [], "feedback": "DATABASE_URL environment variable not found."}

    results = []
    try:
        conn = psycopg2.connect(db_url)
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(sql_query)
            # Only fetch if it's a SELECT
            if cur.description:
                results = cur.fetchall()
            conn.commit()
        conn.close()
        
        # In a real dict cursor, results are already dicts
        # We need to ensure they are serializable lists of dicts
        return {"execution_results": [dict(row) for row in results]}
        
    except Exception as e:
        return {"feedback": f"Execution Error: {str(e)}", "execution_results": None}

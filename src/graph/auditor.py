from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from src.graph.state import AgentState
from src.graph.prompts import AUDITOR_SYSTEM_PROMPT
import os

llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

def auditor_node(state: AgentState) -> AgentState:
    """
    Auditor agent that reviews SQL for security and performance.
    """
    sql_query = state.get("current_sql", "")
    
    messages = [
        SystemMessage(content=AUDITOR_SYSTEM_PROMPT),
        HumanMessage(content=f"SQL to Audit:\n{sql_query}")
    ]
    
    response = llm.invoke(messages)
    content = response.content.strip()
    
    # Check for approval or rejection based on protocol
    if "REJECTED:" in content:
        # Extract the reasoning
        # Format "REJECTED: [Reasoning]"
        parts = content.split("REJECTED:", 1)
        feedback = parts[1].strip() if len(parts) > 1 else "Unknown rejection reason."
        # Keep the SQL but mark feedback so we can loop back
        return {"feedback": feedback}
        
    elif "APPROVED:" in content:
        # If approved, we might want to ensure the SQL is passed through cleanly 
        # distinct from what LLM returned if it modified it, but usually approval means 'current_sql' is fine.
        # We assume 'content' might contain 'APPROVED: <SQL>' or just 'APPROVED: <SQL> ...'
        # For simplicity, we trust the 'current_sql' if the Auditor approved it, 
        # unless Auditor returns a modified version. The prompt says OUTPUT 'APPROVED: [SQL_QUERY]'
        # Let's try to extract it just in case.
        parts = content.split("APPROVED:", 1)
        approved_sql = parts[1].strip() if len(parts) > 1 else sql_query
        
        # Clear feedback to indicate success
        return {"current_sql": approved_sql, "feedback": None}
        
    else:
        # Fallback
        return {"feedback": f"Auditor returned invalid format: {content}"}

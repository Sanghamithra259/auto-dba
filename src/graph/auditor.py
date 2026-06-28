# src/graph/auditor.py
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_groq import ChatGroq  # Changed this
from src.graph.state import AgentState
from src.graph.prompts import AUDITOR_SYSTEM_PROMPT
import os

# 🔄 Update the model string here
llm = ChatGroq(groq_api_key=os.getenv("GROQ_API_KEY"), model="llama-3.1-8b-instant")

# ... rest of your auditor_node function remains exactly the same!

def auditor_node(state: AgentState) -> AgentState:
    sql_query = state.get("current_sql", "")
    
    messages = [
        SystemMessage(content=AUDITOR_SYSTEM_PROMPT),
        HumanMessage(content=f"SQL to Audit:\n{sql_query}")
    ]
    
    response = llm.invoke(messages)
    content = response.content.strip()
    
    # Use case-insensitive checking and split cleanly
    if "REJECTED:" in content.upper():
        parts = content.split("REJECTED:", 1)
        feedback = parts[1].strip() if len(parts) > 1 else "Compliance violation flagged by auditor."
        return {"feedback": feedback}
        
    elif "APPROVED:" in content.upper():
        parts = content.split("APPROVED:", 1)
        approved_sql = parts[1].strip() if len(parts) > 1 else sql_query
        
        # Clean up any accidental markdown blocks the auditor might replicate
        if approved_sql.startswith("```sql"): approved_sql = approved_sql[6:]
        if approved_sql.endswith("```"): approved_sql = approved_sql[:-3]
        
        return {"current_sql": approved_sql.strip(), "feedback": None}
        
    else:
        # Fallback if the model hallucinated the response protocol
        return {"feedback": f"Auditor failed parsing protocol. Output: {content}"}
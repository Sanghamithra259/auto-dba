from langchain_core.messages import SystemMessage, HumanMessage
from langchain_openai import ChatOpenAI
from src.graph.state import AgentState
from src.graph.prompts import ANALYST_SYSTEM_PROMPT
import os
import json

llm = ChatOpenAI(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o")

def analyst_node(state: AgentState) -> AgentState:
    """
    Analyst agent that translates natural language to SQL.
    If feedback exists (from Auditor), it refines the previous SQL.
    """
    schema_str = json.dumps(state.get("schema_json", {}), indent=2)
    user_query = state.get("user_query")
    feedback = state.get("feedback")
    current_sql = state.get("current_sql")
    iteration_count = state.get("iteration_count", 0)

    # Base system prompt
    system_msg = SystemMessage(content=ANALYST_SYSTEM_PROMPT.format(schema_json=schema_str))
    
    # Construct message history based on feedback loop
    messages = [system_msg]
    
    if feedback and current_sql:
        # We are correcting a previous attempt
        messages.append(HumanMessage(content=user_query))
        messages.append(HumanMessage(content=f"Previous SQL attempt: {current_sql}\nFeedback: {feedback}\nPlease fix the SQL based on the feedback."))
    else:
        # First attempt
        messages.append(HumanMessage(content=user_query))
    
    response = llm.invoke(messages)
    sql_query = response.content.strip()
    
    # Clean up markdown
    if sql_query.startswith("```sql"):
        sql_query = sql_query[6:]
    if sql_query.endswith("```"):
        sql_query = sql_query[:-3]
    
    sql_query = sql_query.strip()
        
    return {
        "current_sql": sql_query,
        "iteration_count": iteration_count + 1,
        # Reset feedback since we addressed it, though the graph state update might merge. 
        # In LangGraph, we return the keys we want to update.
        "feedback": None 
    }

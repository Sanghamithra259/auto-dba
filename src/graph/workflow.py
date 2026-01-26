from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph.analyst import analyst_node
from src.graph.auditor import auditor_node
from src.graph.executor import execution_node

def params_auditor(state: AgentState):
    """
    Conditional edge logic:
    - If feedback is present and not None, it means Auditor Rejected -> Loop back to Analyst
    - If feedback is None, it means Auditor Approved -> Go to Execution
    """
    if state.get("feedback"):
        # Auditor rejected or found issue
        return "analyst"
    return "execution"

# Initialize Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("analyst", analyst_node)
workflow.add_node("auditor", auditor_node)
workflow.add_node("execution", execution_node)

# Set Entry Point
workflow.set_entry_point("analyst")

# Add Edges
# Analyst -> Auditor
workflow.add_edge("analyst", "auditor")

# Auditor -> (Conditional) -> Analyst OR Execution
workflow.add_conditional_edges(
    "auditor",
    params_auditor,
    {
        "analyst": "analyst",
        "execution": "execution"
    }
)

# Execution -> END
workflow.add_edge("execution", END)

# Compile
app_graph = workflow.compile()

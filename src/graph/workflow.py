# src/graph/workflow.py
from langgraph.graph import StateGraph, END
from src.graph.state import AgentState
from src.graph.analyst import analyst_node
from src.graph.auditor import auditor_node
from src.graph.executor import execution_node

def params_auditor(state: AgentState):
    """
    Conditional edge logic with an iteration ceiling to stop infinite loops.
    """
    iteration_count = state.get("iteration_count", 0)
    MAX_ITERATIONS = 3

    if state.get("feedback"):
        if iteration_count >= MAX_ITERATIONS:
            # Drop out of the graph gracefully instead of looping infinitely
            return "exit_on_failure"
        return "analyst"
    return "execution"

workflow = StateGraph(AgentState)

workflow.add_node("analyst", analyst_node)
workflow.add_node("auditor", auditor_node)
workflow.add_node("execution", execution_node)

workflow.set_entry_point("analyst")
workflow.add_edge("analyst", "auditor")

workflow.add_conditional_edges(
    "auditor",
    params_auditor,
    {
        "analyst": "analyst",
        "execution": "execution",
        "exit_on_failure": END  # Directly route to END if iteration max is reached
    }
)

workflow.add_edge("execution", END)
app_graph = workflow.compile()
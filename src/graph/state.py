from typing import TypedDict, Optional, List, Dict, Any

class AgentState(TypedDict):
    user_query: str
    schema_json: Dict[str, Any]
    current_sql: Optional[str]
    feedback: Optional[str]
    execution_results: Optional[List[Dict[str, Any]]]
    iteration_count: int

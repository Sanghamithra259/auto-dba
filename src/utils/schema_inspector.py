import re

def parse_ddl_and_generate_snapshot(ddl_string: str) -> dict:
    """
    A lightweight utility that parses simple CREATE TABLE statements 
    and outputs a snapshot dictionary for the AI agents.
    """
    if not ddl_string:
        return {}
        
    snapshot = {"tables": {}}
    
    # Simple regex to extract table name and column block
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

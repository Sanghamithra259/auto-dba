# Auto-DBA

An enterprise-grade, multi-agent compliance engine that securely translates natural language financial questions into safe, optimized PostgreSQL queries and executes them directly against a production database instance. 

Built with an **Analyst-Auditor feedback loop architecture**, the system actively intercepts malicious inputs, self-corrects compliance violations at the runtime boundary, and enforces a strict read-only execution ledger.

---

## Architecture & Technology Stack

* **Orchestration Framework:** LangGraph (StateGraph lifecycle engine)
* **Database Infrastructure:** Supabase (PostgreSQL engine)
* **API Delivery Routing:** FastAPI (Asynchronous ASGI application)
* **Package Management & Virtualization:** `uv` (Fast Python dependency installer and environment sync)
* **Deployment Configuration:** Google Cloud Run containerized via Docker

---

##  System Execution Lifecycle

The multi-agent execution workflow utilizes a state machine logic context loop. Instead of directly executing raw text transformations, the operational pipeline applies multi-layered evaluation gates:

1. **Analyst State Mutation (`analyst_node`):** Ingests the natural language input along with dynamic database schema snapshots (JSON format) and maps the semantics to explicit ANSI SQL statements.
2. **Compliance Auditing Gate (`auditor_node`):** Evaluates the query string under strict compliance configurations (e.g., matching data structure access policies, regex-free verification flags, and structural safety limitations).
3. **Conditional State Feedback Routing:** * **Approval Pass:** If the Auditor parses an `APPROVED:` token payload, the query state is passed downstream to the execution driver.
   * **Rejection Optimization Loop:** If the Auditor yields a `REJECTED:` payload, precise contextual feedback string errors are routed back to the Analyst for programmatic self-correction (capped at a ceiling of 3 iterations to completely eliminate infinite loop resource consumption).
4. **Driver Guard Interception Boundary (`execution_node`):** A rigid programmatic fallback interceptor confirms the lack of mutating operations (`DROP`, `DELETE`, etc.) at the engine driver level before committing transactions via `psycopg2` tracking cursors against Supabase.

---

##  Local Installation & Execution Environments

### Prerequisites
Ensure your local development environment has `curl` capabilities and a valid Python environment.

### 1. Install the `uv` Package Manager
Execute the automated platform-specific installation script:
```bash
curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
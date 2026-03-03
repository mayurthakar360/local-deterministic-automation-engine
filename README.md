\# Local Deterministic Automation Engine



A deterministic, plugin-driven automation runtime designed for controlled multi-step execution with governance, traceability, and replay support.



---



\## 🚀 Overview



This engine provides:



\- Deterministic multi-step planning

\- Plugin-based execution architecture

\- Risk-based governance (Low / Medium / High)

\- Distributed trace propagation (agent → executor)

\- Strict idempotency (request-level protection)

\- Execution replay via trace\_id

\- Step-level timeout control

\- Deterministic failure stop

\- Plan versioning (v1.0.0)



---



\## 🏗 Architecture



Client  

→ Agent Service (Planner \& Governance)  

→ Executor Service (Tool Runtime)  

→ Plugin Layer  



---



\## 📦 Project Structure

agent\_service/

executor\_service/

plugins/

shared/

logs/





---



\## 🧠 Core Principles



\- Determinism over heuristics

\- Governance over unrestricted execution

\- Bounded execution over indefinite processing

\- Replayability over hidden state

\- Versioned planner evolution



---



\## 🏷 Current Version



\*\*v1.0.0 — Core Runtime Stable\*\*



Includes:

\- Plugin-driven filesystem tools

\- Trace propagation

\- Idempotency protection

\- Timeout guard

\- Plan versioning



---



\## 🔮 Future Roadmap



\- Persistent idempotency store

\- Planner v2 framework

\- External tool integrations

\- Distributed scaling

\- Cooperative cancellation support



---



\## 📄 License



No license specified.


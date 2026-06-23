# ArchSpec AI: Autonomous Architectural Material Specification & Multi-Tier Procurement Marketplace

An enterprise-grade, non-linear AI state-graph workflow tailored for the AEC (Architecture, Engineering, and Construction) industry. This platform automates building material visual extraction, cost-estimation matrix processing, and smart routing for local vendor procurement.

## 🛠️ Architecture & Core Components

- **`agent_graph.py`**: Core AI state-graph implementation. Manages non-linear execution states, vision-based material extraction, and multi-tier pricing validation with automated safety branching.
- **`main_dashboard.py`**: Production-ready FastAPI web server powering the high-fidelity Glassmorphic user interface, offering live status monitoring and human-in-the-loop (HITL) action triggers.
- **`mcp_server.py`**: FastMCP server integrating the Model Context Protocol (MCP) to serve as a secure gateway connecting model runtimes directly to dynamic material databases.
- **`vendors_db.json`**: Structural JSON registry holding regional material benchmarks, multi-tier pricing models, and verified supplier lists.
- **`validate_flow.py`**: Autonomous validation layer designed to dynamically simulate agent execution runs and verify logic integrity.

## 🚀 Key Features

- **Asynchronous Visual Ingestion**: Automatically analyzes 3D renders or schematic layouts to harvest structural spec lists.
- **Human-in-the-Loop (HITL) Safety Check**: Halts execution, displays computed material costs, and freezes state variables, waiting for the Design Architect validation before initiating commercial connection.
- **Multi-Tier Procurement Routing**: Instantly routes verified specs to optimized local building suppliers and trade networks once authorized.

---
*Developed under the Business Automation & Workflows Track.*

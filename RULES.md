# ESPHamClock - Project Rules & Mandates

This document serves as the primary source of truth for all project mandates, operational rules, and architectural guidelines. Every contributor and agent MUST adhere to these standards.

## 1. Critical Project Mandates

1.  **SERVICE MANAGEMENT**: ALWAYS use `./run_stack.sh` for starting, stopping, or checking status of any project component. Never run `server.py` or other main binaries directly unless debugging a specific failure that `run_stack.sh` cannot handle.
2.  **WORKFLOWS**: Refer to `.agent/workflows/` for standard operating procedures. Specifically, use `manage-stack.md` for service control.
3.  **LOGGING**: NEVER capture transient logs, debug outputs, or analysis dumps in `/tmp`. ALWAYS use the project `logs/` directory for persistence and visibility.
4.  **CACHING**: This project relies heavily on file-based caching in `backend/data/processed_data/`. Always check for existing cached data before fetching from upstream.
5.  **PARITY**: The goal is 1:1 parity with the original HamClock backend. Every line/pixel counts.
6.  **NO CLIENT CHANGES**: NEVER modify the `client/` source code. The goal is to create a fully functional replacement backend for ALL existing clients. All issues must be resolved on the backend or proxy layers.

---

## 2. Detailed Architectural Rules

### Standardized Debugging Outputs
To maintain a clean project root and prevent transient debugging data from being accidentally committed to the repository, all debugging outputs MUST be directed to a dedicated `debug/` directory.

- **Location**: All transient files (logs, captures, temporary data, result summaries) must be stored within `debug/` at the project root.
- **Exclusion**: The `debug/` directory MUST be included in the project's `.gitignore` file.
- **Organization**: Use subdirectories (e.g., `debug/logs/`, `debug/captured_data/`) to organize outputs.

### Client Code Stability & Backend Compatibility
To achieve the project's core objective of providing a fully functional replacement backend for all existing HamClock clients, the client-side source code MUST NOT be modified for feature enhancements or bug fixes that can be resolved on the backend.

- **Drop-in Replacement**: Modifying the client breaks the "drop-in replacement" promise. If we modify the client to handle backend limitations, we lose compatibility with original hardware.
- **Backend Adaptation**: The backend must adapt to the client's expectations (e.g., line limits, data intervals, formats).
- **Parity Validation**: Every change must be validated against the behavior of existing clients to ensure seamless transition.

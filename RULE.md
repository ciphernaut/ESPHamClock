# Rule: Standardized Debugging Outputs

To maintain a clean project root and prevent transient debugging data from being accidentally committed to the repository, all debugging outputs MUST be directed to a dedicated `debug/` directory.

## Requirements

1. **Location**: All transient files (logs, captures, temporary data, result summaries) generated during development/debugging must be stored within the `debug/` directory at the project root.
2. **Exclusion**: The `debug/` directory MUST be included in the project's `.gitignore` file.
3. **Subdirectories**: Projects are encouraged to use subdirectories within `debug/` (e.g., `debug/logs/`, `debug/captured_data/`) to organize outputs.
4. **Cleanup**: Existing transient files currently in the root or other non-standard locations should be migrated or deleted.

## Rationale

The project root has previously been cluttered with over 100 transient files (e.g., `*.txt`, `*.bin`, `*.log`), making it difficult to find source files and increasing the risk of "sneaky" commits that include temporary data. Consolidating these into an ignored directory ensures a clean and manageable workspace.

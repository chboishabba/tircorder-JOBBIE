# Update Log

## Scanner and state handling
- Scanner now records each discovered file in the database and queues its ID for downstream work, preventing mismatched references.
- State loading reconstructs the known-files cache from folder paths and filenames so change detection remains reliable.


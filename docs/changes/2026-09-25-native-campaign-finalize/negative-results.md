# Required negative results

The implementation must reject or block:

- runtime binary/version drift;
- command digest drift or duplicate stage commands;
- source contract, ADK source or rendered bundle drift;
- non-UTF-8/failed version probe or version mismatch;
- output flood and stage timeout;
- discovery/load/trigger non-zero exit;
- finalize after any failed or blocked stage;
- receipt output path differing from the frozen plan;
- direct overwrite of the active target contract.

Synthetic commands are software-only fixtures. A green fixture never implies a native target is certified.

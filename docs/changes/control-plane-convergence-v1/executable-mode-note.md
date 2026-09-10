# Executable Mode Note

New shell regressions are required to be tracked as executable files because `tests/run_all.sh` invokes them directly. Git mode is part of the test contract, not a local chmod side effect.

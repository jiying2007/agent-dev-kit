# Native campaign/finalize requirements

1. Freeze source contract, rendered bundle, runtime binary/version, trust authority/backend and stage command digests before execution.
2. Version probe must use the exact runtime binary and confirm the planned version.
3. Discovery/load/trigger commands must be independent and execute in one isolated target bundle.
4. The runner must use a minimal environment, bounded output, bounded time and no shell.
5. Raw commands, stdout/stderr, credentials, prompts and messages must not be persisted.
6. Failure or block at any stage must prevent receipt finalization.
7. Finalize must emit the existing typed native conformance receipt and a future runtime target contract, but must not overwrite the active contract.
8. Receipt signing, managed trust registry binding and target promotion remain separate owner-reviewed steps.
9. Public CLI capability advances source version to 7.4.0.

# Native campaign process deadline — tasks

- [x] Identify launcher-exit versus inherited-pipe-EOF timeout gap in the current source
- [x] Bind the complete process/pipe lifecycle to one deadline
- [x] Kill POSIX descendant process group even after launcher exit and join canceled readers
- [x] Add bounded negative regression in the existing native campaign test suite
- [x] Document runtime behavior and preserve privacy/trust separation

The protected-PR CI, exact-main signed release and Root promotion are independently verified workflow stages; this document does not claim their outcome.

# Tasks

- [x] Replace permissive JSON decoding with canonical strict decoding and bounded regular-file capture.
- [x] Cover strict JSON, bounded source files, MCP command/args/header/env/URL literal credentials, encoded URL userinfo, scheme/port invalid inputs, symlink/FIFO/directory config inventory, managed placeholders and opaque evidence refs; preserve review boundaries.
- [x] Synchronize patch SemVer 8.1.2 and changelog.
- [ ] Pass exact PR CI across supported Python versions.
- [ ] Pass fresh-main CI and immutable signed release.
- [ ] Promote Root using verified release evidence, never copied historical qualification.

G21, G22 and LTA-04 remain separate authentic-evidence blockers.

- [x] Add URL authority backslash/encoded-delimiter, invalid percent escape and empty-auth query/userinfo fail-closed tests after Review #5663083519.

- [x] Reject pre-normalization URL whitespace/C0/C1 and encoded C0/DEL; classify empty env/header/command credentials as needs-review and add integrated positive/negative cases.

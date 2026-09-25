# Native campaign project-layout checkpoint

- [x] Add reviewed native campaign target-layout manifest for all direct targets.
- [x] Bind Claude Code to project `.claude` and OpenCode to project `.opencode`.
- [x] Execute stages from isolated project root while writing the rendered target bundle into the project config root.
- [x] Preserve HOME auth separately and expose explicit project/config root environment variables.
- [x] Add cross-target regression that verifies cwd/config-root/skills layout.
- [x] Keep campaign v1 plan/evidence/receipt contracts unchanged.
- [x] Advance source identity to 7.4.1.
- [ ] Final PR CI, fresh-main CI, immutable release and Root promotion must come from actual GitHub runs.
- [ ] A real authenticated runtime campaign remains external evidence; this patch only makes that future campaign target the correct native project surface.

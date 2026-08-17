# Full Quiet OSS reference

Sixies vendors one host-side analyzer from Damian Yerrick and Retrotainment
Games' Full Quiet OSS collection.

- Upstream: https://github.com/pinobatch/full-quiet-oss
- Pinned commit: `5b7edb7767308b39f627616e092079e378ce85cf`
- Commit date: 2025-06-06
- Vendored tool: `tools/ld65ramuse.py`
- Tool SHA-256:
  `ebbe768d77f9399eb9c531e323d6dd2114078586259a0e5a696a759694af6c5a`

The tool is retained unchanged and runs through `make nes-usage`. It reads the
ld65 map generated for the current ROM and reports each object's contribution
to every segment. The complete Apache License 2.0 is retained in `LICENSE`.

The upstream `nstripes.py` and `strips.py` tools are intentionally not vendored
yet. They require Pillow, and their generated data or sample runtime should be
integrated only when Sixies reaches the background-effect and animated
metasprite milestones. `pack8k.py` likewise remains deferred until the port
selects a bank-switched mapper.

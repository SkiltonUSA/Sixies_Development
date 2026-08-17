# segaloco fc_tools reference

The Sixies NES graphics pipeline uses the file-format behavior documented by
Matthew Gilmore's `fc_tools` project as a reference for CHR rendering,
nametable-to-CHR expansion, metatile expansion, and iNES component inspection.

- Upstream: https://gitlab.com/segaloco/misc/-/tree/master/fc_tools
- Pinned commit: `c0c1b1731d177015a079a56ca147af4b65c64652`
- Commit date: 2026-08-14
- Relevant tools: `chrtopng`, `nttochr`, `mttont`, and `ddnes`

No upstream executable source is compiled or required by this repository.
Equivalent checked and dependency-free implementations live in
`scripts/nes_graphics.py`. The selected upstream files carry the BSD 3-Clause
license; its notice is preserved below.

## BSD 3-Clause notice

Copyright 2025-2026 Matthew Gilmore

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice,
   this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.
3. Neither the name of the copyright holder nor the names of its contributors
   may be used to endorse or promote products derived from this software
   without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

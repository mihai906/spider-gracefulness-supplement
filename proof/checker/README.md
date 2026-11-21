# Logos checker

`logos` is the CPC proof checker Logos (https://github.com/cvc5/logos),
built at commit `a4ab2f8deada090d96178ee9da22a47b5c834e33` with Lean
toolchain `leanprover/lean4:v4.34.0`. The executable targets x86-64 Linux
with glibc.

`source/` is the upstream source tree at that commit. To build the
checker on another system, follow `source/README.md`
(`scripts/build.sh logos`). The resulting executable is
`.lake/build/bin/logos`.

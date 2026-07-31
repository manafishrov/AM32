# AGENTS.md

## Purpose

Manafish-maintained fork of AM32 firmware for the ROV's brushless-motor ESCs.
It receives DShot commands from `mcu-firmware`. The fork carries Manafish motor
control, startup, current, temperature, and stall-protection behavior that
upstream AM32 does not intend to merge.

## Fork model

- `origin` is `https://github.com/manafishrov/AM32.git` and is the product
  repository.
- `upstream` is `https://github.com/am32-firmware/AM32.git` and is a source for
  selectively imported fixes.
- Manafish changes belong on this fork's `main`; they do not require upstream
  acceptance.
- `origin/manafish-changes` is the pre-consolidation Manafish history. The
  `chore/am32-fork-setup` branch carries that history for promotion to `main`.
- Never reset Manafish history to upstream. Review upstream updates and merge
  or cherry-pick them deliberately, then revalidate the affected targets.

## Stack and structure

- C firmware for ARM-based ESCs
- GNU Arm Embedded toolchains and Make
- `Src/` — shared firmware logic
- `Inc/` — headers, targets, settings, and version
- `Mcu/` — MCU-specific drivers, linker scripts, and startup code
- `Keil_Projects/`, `MRS_Projects/` — vendor IDE projects
- `*makefile.mk`, `make/`, `Makefile` — target definitions and build tooling
- `obj/` — generated binaries

Manafish currently targets the F421 path. Changes to shared code still need to
compile for every target because CI builds the full matrix.

## Commands

Install the pinned build toolchains once:

```sh
make arm_sdk_install
```

List board targets or build everything:

```sh
make targets
make -j"$(nproc)"
```

Build a single target by using a name printed by `make targets`. Remove build
outputs with `make clean`.

### Quality

Before merging firmware changes:

```sh
make -j"$(nproc)"
```

CI performs the same all-target build on Linux and Windows. For documentation-
only changes, at minimum run `git diff --check` and verify all local links.

`format.sh` rewrites C and header files in place; inspect its diff before
keeping any formatting changes.

## Rules

- Preserve the Manafish safety behavior in `Src/main.c`: back-EMF duty
  limiting, startup duty caps, stall detection, and temperature lockout.
- Coordinate DShot or telemetry behavior changes with `../mcu-firmware` and
  any host-side consumers.
- Treat linker script and Keil project changes as part of the firmware change;
  GCC and Keil builds must describe the same memory layout.
- Do not import upstream changes wholesale without reviewing conflicts against
  Manafish motor-control behavior.
- Do not add generated files from `obj/`.
- Do not push without being asked. CI builds on pushes and pull requests to
  `main`; version tags may publish release artifacts.

## Commits

Use Conventional Commits with an imperative, lowercase subject:

```text
<type>(<scope>): <subject>
```

Types: `feat`, `fix`, `refactor`, `perf`, `docs`, `chore`, `ci`, `build`,
`revert`. Useful scopes include `control`, `safety`, `startup`, `telemetry`,
`f421`, `targets`, `build`, and `ci`.

## Keep this file useful

Update this file when the supported Manafish hardware, fork strategy, build
commands, release path, or quality gates change.

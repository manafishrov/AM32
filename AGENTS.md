# AGENTS.md

## Purpose

Manafish-maintained fork of AM32 firmware for the ROV's brushless-motor ESCs.
It receives DShot commands from `mcu-firmware`. The fork carries Manafish motor
control, startup, current, temperature, and stall-protection behavior that
upstream AM32 does not intend to merge.

## Fork model

- `origin` is `git@github.com:manafishrov/AM32.git` and is the product
  repository.
- `upstream` is `https://github.com/am32-firmware/AM32.git` and is a source for
  selectively imported fixes.
- Manafish changes belong on this fork's `main`; they do not require upstream
  acceptance.
- `origin/manafish-changes` preserves the pre-consolidation branch name. New
  product work belongs on branches from `main`.
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

The Manafish product target is `SKYSTARS_AM60_V2_F421`. Changes to shared F421
code still need to compile for the full F421 family.

## Commands

Install the pinned build toolchains once:

```sh
make arm_sdk_install
```

Build the Manafish product, validate the F421 family, or list board targets:

```sh
make product
make -j"$(nproc)" f421
make targets
```

Build a single target by using a name printed by `make targets`. Remove build
outputs with `make clean`.

### Quality

Before merging firmware changes:

```sh
make -j"$(nproc)" f421
```

CI builds the full F421 family on Linux and the Manafish product target on
Windows. For documentation-only changes, at minimum run `git diff --check` and
verify all local links.

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

## Releases

**Never cut a release without being explicitly asked, and confirm the version
and release notes back to the user before doing anything.**

- AM32 releases use SemVer independently of the other Manafish firmware.
- Bump `VERSION_MAJOR`, `VERSION_MINOR`, and `VERSION_PATCH` in
  `Inc/version.h` to match `vX.Y.Z`.
- Commit message: `chore(release): vX.Y.Z`.
- Tag: `git tag vX.Y.Z` then `git push --tags`.
- Pushing the tag triggers `.github/workflows/build.yml`, which validates the
  tag against the header, builds `SKYSTARS_AM60_V2_F421`, attaches its `.hex`
  and raw application `.bin` files, checksums, and updater manifest, and
  creates a **draft** GitHub release.
- Pre-releases use `vX.Y.Z-rc.N` and are automatically marked prerelease.
- Quality gates above must pass before tagging.

Workflow before tagging: confirm the bumped version with the user, confirm the
release notes text, then commit, tag, and push.

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

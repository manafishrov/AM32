# Manafish AM32 firmware

Manafish-maintained fork of [AM32](https://github.com/am32-firmware/AM32) for
the ROV's brushless-motor ESCs. It is kept as an independent fork because the
Manafish motor-control and safety behavior is specific to the vehicle and is
not intended for upstream AM32.

The fork currently focuses on the F421 target and includes Manafish-specific
startup behavior, low-speed and stall protection, back-EMF duty limiting,
current limiting, temperature lockout, and startup audio.

## Repository model

- `origin` — [`manafishrov/AM32`](https://github.com/manafishrov/AM32), the
  maintained Manafish firmware
- `upstream` — [`am32-firmware/AM32`](https://github.com/am32-firmware/AM32),
  used to selectively import relevant fixes

Manafish development and releases happen from this repository. Upstream
changes should be reviewed against the Manafish safety behavior before they
are merged.

## Build

Install the ARM toolchains once, then build the Manafish product:

```sh
make arm_sdk_install
make product
```

Validate all F421 targets with `make -j"$(nproc)" f421`. Run `make targets` to
list every upstream board target. Generated `.bin`, `.elf`, and `.hex` files
are written to `obj/`.

## Releases

Manafish releases follow Semantic Versioning. The version is stored in
`Inc/version.h`, and release tags use `vX.Y.Z` (or `vX.Y.Z-rc.N` for a
prerelease). A version tag builds `SKYSTARS_AM60_V2_F421` and creates a draft
GitHub release containing its `.hex` file and checksum.

## License

This fork remains licensed under the GNU General Public License v3.0. See
[LICENSE](LICENSE). The original AM32 project and its contributors retain
their respective copyrights.

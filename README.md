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

Install the ARM toolchains once, then build all supported targets:

```sh
make arm_sdk_install
make -j"$(nproc)"
```

Run `make targets` to list individual board targets. Generated `.bin`, `.elf`,
and `.hex` files are written to `obj/`.

## License

This fork remains licensed under the GNU General Public License v3.0. See
[LICENSE](LICENSE). The original AM32 project and its contributors retain
their respective copyrights.

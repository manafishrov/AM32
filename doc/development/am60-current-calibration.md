# AM60 V2 current calibration

The Manafish `SKYSTARS_AM60_V2_F421` target applies the empirical correction
`board_current_A = 91 - legacy_board_current_A`. This is specific to the
Manafish-tested ESC boards, not a calibration for all four-in-one ESCs.

The target previously used `CURRENT_OFFSET = 0` and
`MILLIVOLT_PER_AMP = 20`. It now uses an offset of 1820 mV and sensitivity
of -20 mV/A. The 1820 mV value expresses the observed 91 A legacy baseline
in the existing conversion's units; it is not an independently measured
sensor voltage. Conversion happens in `Src/main.c` before the existing
negative-current clamp and telemetry encoding. Shared conversion code and
other targets are unchanged.

## Reporting and rounding

All four controllers on one board report its shared sensor. The Pi must
continue averaging those copies, then summing the two board averages. Before
telemetry rounding, the total is approximately
`max(0, 91 - legacy_board1_A) + max(0, 91 - legacy_board2_A)`.
This reduces to `182 - legacy_total_A` only when both legacy board readings
are at most 91 A. Each board is clamped independently before aggregation.
Do not apply another correction in the Pi or app.

AM32 keeps current in 0.01 A units and truncates DShot EDT current to whole
amperes. Correcting before that truncation can differ by up to about 1 A per
board from subtracting an old, already-truncated display reading from 91.
The correction is not applied to the transmitted byte or to the two-board
aggregate inside an individual ESC.

## Protection implications

The calibrated `actual_current` feeds current telemetry, consumed-capacity
accounting, and the measured-current limiter when enabled. This change does
not modify its enable setting, threshold, PID gains, or saved EEPROM values.
The default is disabled, but preserved settings must be read back to establish
what is actually enabled on installed controllers.

The custom back-EMF duty cap, startup cap, stall detection/cooldown, and thermal
lockout do not consume this current measurement and are unchanged. An enabled
measured-current limiter can still change applied duty and interact with them.
Each controller measures board current, not individual motor current.

The software correction alone does not validate the ADC input, sensor circuit,
current limiting, or fast electrical protection. This conversion can represent
at most 91 A per board (ADC zero); negative results are clamped to zero. Do not
infer protection above that range or treat a zero reading as proof of safety.

## Validation and rollout

Run the host regression tests with a native C compiler and Python 3:

```sh
python3 tests/test_current_calibration.py
make -j"$(nproc)" f421
```

The tests compile the production 12-bit ADC expression, negative-current clamp,
and EDT encoder with the real target definitions. They cover every 12-bit ADC
code, polarity, idle offset, clamping, two-board reporting, and an unaffected
F421 target. These are software tests, not sensor or protection measurements.

Before hardware rollout, read the saved settings from all eight controllers,
check each board against independent current measurements over the intended
operating range, and validate any enabled current limiting under controlled
loads. Account for accessories outside the ESC sensors when comparing against
battery current. Corrected telemetry requires all four controllers on each
board to run the calibrated image; mixed old/new readings make averaging
incorrect.

No wire-format, unit, EEPROM-layout, Pico, or app change is required. Publishing
an AM32 release and updating the Pi's bundled ESC image are separate,
explicitly authorized steps. No downstream `182 - total` correction should be
combined with this firmware.

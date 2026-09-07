# AM60 V2 current reporting

The fixed 1820 mV offset and negative sensitivity have been reverted. Field
observations showed that the idle total varies (for example 182, 176, or 174),
so a fixed `182 - total` correction is not reliable.

The target again uses `CURRENT_OFFSET = 0` and `MILLIVOLT_PER_AMP = 20`, preserving
the original uncorrected EDT readings. This is not a claim that the sensor is
correctly calibrated. It lets the Pico observe the variable idle baseline
without the fixed inverse conversion clamping away information.

The paired Pico implementation reports incremental board current relative to a
stable idle baseline. Raw type-3 EDT current remains available for diagnosis.
This reporting-only correction does not repair AM32's measured-current limiter
or consumed-capacity accounting. Do not rely on those as calibrated current
protection. Current-limit settings and the custom sensorless protection are
unchanged; installed EEPROM settings still need readback and hardware validation.

The AM60 input-settings policy remains in place. Install an AM32 image containing
both this revert and that policy on all eight controllers before the new Pico.
The host/app must understand unavailable calibrated current before upgrading the
Pico; older host firmware will continue displaying uncorrected raw readings.
Do not apply an additional fixed-offset correction in the app or Pi.

Validation:

```sh
python3 tests/test_current_calibration.py
python3 tests/test_input_settings.py
make -j"$(nproc)" f421
```

Tests cover all ADC codes, raw telemetry units, encoding limits, and an unaffected
target. They do not validate the sensor circuit, amperes-per-unit gain, battery
current, or electrical protection.

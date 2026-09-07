# AM60 V2 input settings

`SKYSTARS_AM60_V2_F421` owns the input configuration required by the Manafish
Pico firmware. The target applies these settings after loading EEPROM and
before every application settings save:

| Setting | Required value |
| --- | --- |
| Input protocol | Automatic detection |
| Bidirectional mode | Enabled |
| PWM low/high endpoints | 1000 / 2000 microseconds |
| PWM neutral | 1500 microseconds |
| PWM deadband | Existing product value, 3 |
| Stick-based calibration | Disabled |

This is a targeted normalization, not an EEPROM reset or schema-version bump.
For current-version EEPROM, only these seven bytes are changed by the policy.
An incompatible saved value marks settings dirty and triggers the existing
boot-time save. A subsequent boot with matching settings does not write again.
An explicit save request still writes settings, while reapplying the policy so
it cannot persist a conflicting input configuration. Existing older-version
migration behaviour is unchanged.

Stored motor direction, RC-car mode, current-limit settings, motor parameters,
and protection settings are outside this policy. Their existing runtime
behaviour is unchanged. In particular, this is not a reset of all controller
configuration, nor a guarantee that every other saved mode suits a thruster.
The existing DShot command decoder remains available; this policy establishes
boot/save configuration rather than rejecting every possible external runtime
settings command.

## Why it matters for PWM

A controller saved in forward-only mode interprets a 1500 microsecond pulse as
throttle instead of neutral. A mismatched saved neutral can do the same even
in bidirectional mode. AM32 requires neutral input to arm. DShot stop does not
use the PWM endpoint/neutral mapping, so working DShot does not validate those
settings.

A host reproduction using the production PWM conversion and input mapping
showed both failures and restored neutral acceptance with the required values.
This does not establish that the installed failing controllers had those
settings, or rule out input-circuit/detection-timing problems. Hardware testing
is still required; the Pico's PWM ready acknowledgement is not an ESC arming
acknowledgement.

## Pico command cleanup and rollout

The paired `mcu-firmware` change removes automatic 3D-mode and Save Settings
commands. It retains Extended DShot Telemetry enable and retries because those
are volatile session handshakes, not persistent EEPROM configuration. Neutral
commands, version discovery, and update-recovery handling remain necessary.

Install the AM32 image containing this policy on all eight controllers using
the existing Pico firmware first. Only then install the Pico image that stops
sending setup commands. Other ESC targets are unchanged and require their own
compatible bidirectional configuration before using that Pico image.

Publishing both images does not establish installation order. In particular,
a Pi image that auto-updates its bundled Pico firmware can install the new
Pico before the operator flashes ESCs. Stage the rollout so the ESC update
happens first; do not rely on a simultaneous bundle update to enforce this.
No USB format, EEPROM layout, or app sensor-topology change is required.

## Validation

```sh
python3 tests/test_input_settings.py
python3 tests/test_current_calibration.py
make -j"$(nproc)" f421
```

The input-settings tests compile the real EEPROM layout, load prefix, product
policy, boot-save condition, and save function against mocked flash. They check
current and older-version loading, one-time persistence, later saves,
byte-for-byte preservation outside the policy, and an unaffected F421 target.
They do not run the remaining motor initialization or access hardware.

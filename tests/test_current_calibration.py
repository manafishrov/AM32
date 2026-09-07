#!/usr/bin/env python3
"""Host regression tests for the production ADC conversion and EDT encoder.

Run with: python3 tests/test_current_calibration.py
Requires a native C compiler (CC, default cc). No ESC hardware is accessed.
"""

import ctypes
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


def source_match(pattern, source):
    matches = re.findall(pattern, source, re.DOTALL)
    if len(matches) != 1:
        raise AssertionError("Production seam changed; update the extraction explicitly")
    return matches[0]


class CurrentCalibrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="am32-current-")
        cls.addClassCleanup(cls.temp.cleanup)
        main = (ROOT / "Src/main.c").read_text()
        # Compile the actual 12-bit conversion and negative-current clamp rather
        # than maintaining a second implementation of firmware arithmetic.
        conversion = source_match(
            r"(actual_current = [^;\n]*smoothed_raw_current \* 3300 / 41[^;\n]*;)",
            main,
        )
        clamp = source_match(
            r"(if \(actual_current < 0\) \{\s*actual_current = 0;\s*\})", main
        )
        edt = source_match(
            r"(static uint8_t current_to_edt_amps\(int16_t current_centiamps\).*?\n\})",
            (ROOT / "Src/dshot.c").read_text(),
        )
        source = Path(cls.temp.name) / "current.c"
        source.write_text(
            '#include <stdint.h>\n#include "targets.h"\n'
            + edt
            + "\nint convert(int32_t smoothed_raw_current) {\nint16_t actual_current;\n"
            + conversion + "\n" + clamp + "\nreturn actual_current;\n}\n"
            + "int encode(int value) { return current_to_edt_amps(value); }\n"
        )
        cls.converters = {}
        for target in ("SKYSTARS_AM60_V2_F421", "SKYSTARS_KO60_F421"):
            library = Path(cls.temp.name) / (target + ".so")
            subprocess.run(
                shlex.split(os.environ.get("CC", "cc"))
                + ["-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                   "-I", str(ROOT / "Inc"), "-D" + target, str(source), "-o", str(library)],
                check=True,
            )
            dll = ctypes.CDLL(str(library))
            dll.convert.argtypes = [ctypes.c_int32]
            dll.convert.restype = ctypes.c_int
            dll.encode.argtypes = [ctypes.c_int]
            dll.encode.restype = ctypes.c_int
            cls.converters[target] = dll
        cls.product = cls.converters["SKYSTARS_AM60_V2_F421"]
        cls.other = cls.converters["SKYSTARS_KO60_F421"]

    def test_preserves_raw_offset_and_polarity_for_mcu_auto_zero(self):
        for adc in range(4096):
            expected = (adc * 3300 // 41) // 20
            self.assertEqual(self.product.convert(adc), expected)
        # Do not erase the varying idle offset before the MCU can observe it.
        self.assertEqual(self.product.encode(self.product.convert(2262)), 91)
        self.assertGreater(self.product.convert(2200), self.product.convert(2000))

    def test_adc_limits_do_not_wrap(self):
        self.assertEqual(self.product.convert(0), 0)
        self.assertGreater(self.product.convert(4095), 0)
        self.assertLess(self.product.convert(4095), 32768)

    def test_edt_units_and_saturation_are_unchanged(self):
        for centiamps, amps in ((0, 0), (99, 0), (100, 1), (500, 5),
                               (1000, 10), (25500, 255), (30000, 255)):
            self.assertEqual(self.product.encode(centiamps), amps)

    def test_other_target_retains_legacy_conversion(self):
        for adc in range(4096):
            self.assertEqual(self.other.convert(adc), (adc * 3300 // 41) // 20)


if __name__ == "__main__":
    unittest.main(verbosity=2)

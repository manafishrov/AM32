#!/usr/bin/env python3
"""Compile the production settings policy, load prefix, and save path on a host.

No hardware access. AM32_TEST_REVISION optionally selects a Git baseline.
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


def source(path):
    revision = os.environ.get("AM32_TEST_REVISION")
    if revision:
        return subprocess.check_output(
            ["git", "-C", str(ROOT), "show", revision + ":" + path], text=True
        )
    return (ROOT / path).read_text()


def function(text, signature):
    start = text.index(signature)
    opening = text.index("{", start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (text[end] == "{") - (text[end] == "}")
        end += 1
    return text[start:end]


class InputSettingsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="am32-input-settings-")
        cls.addClassCleanup(cls.temp.cleanup)
        folder = Path(cls.temp.name)
        # eeprom.h includes the MCU's main.h; only integer types are needed here.
        (folder / "main.h").write_text("#include <stdint.h>\n")
        for name in ("eeprom.h", "version.h", "targets.h"):
            (folder / name).write_text(source("Inc/" + name))
        main = source("Src/main.c")
        helpers = re.search(
            r"(#ifdef SKYSTARS_AM60_V2_F421\nstatic void require_input_setting.*?)"
            r"(?=void loadEEpromSettings)", main, re.DOTALL
        )
        start = main.index("void loadEEpromSettings()")
        end = main.index("    // eepromBuffer.advance_level", start)
        # Stop before unrelated derived motor settings/hardware initialization.
        load_prefix = main[start:end] + "}\n"
        boot_save = re.search(
            r"if \(VERSION_MAJOR != eepromBuffer.version.major.*?"
            r"saveEEpromSettings\(\);\s*\}", main, re.DOTALL
        ).group()
        input_enum = re.search(
            r"enum inputType \{.*?\};", source("Inc/common.h"), re.DOTALL
        ).group()
        harness = r'''
#include <stddef.h>
#include <stdint.h>
#include <string.h>
#include "eeprom.h"
#include "version.h"
#include "targets.h"
EEprom_t eepromBuffer;
static EEprom_t stored;
static uint8_t eeprom_settings_dirty;
static unsigned writes;
static uint32_t eeprom_address;
void read_flash_bin(uint8_t* data, uint32_t address, int length) {
    (void)address; memcpy(data, stored.buffer, length);
}
void save_flash_nolib(uint8_t* data, int length, uint32_t address) {
    (void)address; memcpy(stored.buffer, data, length); writes++;
}
'''
        harness += input_enum + "\n" + (helpers.group(1) if helpers else "")
        harness += load_prefix + function(main, "void saveEEpromSettings()")
        harness += "\nvoid boot(void) { eeprom_settings_dirty = 0; loadEEpromSettings();\n"
        harness += boot_save + "\n}\n"
        harness += r'''
void seed(void) {
    memset(&stored, 0x55, sizeof stored);
    stored.eeprom_version = EEPROM_VERSION;
    stored.version.major = VERSION_MAJOR;
    stored.version.minor = VERSION_MINOR;
    stored.brake_on_zero_throttle = 0; // Already valid; not a legacy repair case.
    stored.bi_direction = 0;
    stored.input_type = DSHOT_IN;
    stored.disable_stick_calibration = 0;
    stored.servo.neutral = 146; // 1520 us
    eepromBuffer = stored;
    writes = 0; eeprom_settings_dirty = 0;
}
static const size_t offsets[] = {
    offsetof(EEprom_t, input_type), offsetof(EEprom_t, bi_direction),
    offsetof(EEprom_t, servo.low_threshold), offsetof(EEprom_t, servo.high_threshold),
    offsetof(EEprom_t, servo.neutral), offsetof(EEprom_t, servo.dead_band),
    offsetof(EEprom_t, disable_stick_calibration)
};
int policy_offset(int i) { return offsets[i]; }
int read_byte(int i) { return eepromBuffer.buffer[i]; }
int stored_byte(int i) { return stored.buffer[i]; }
int write_count(void) { return writes; }
void disturb_policy(void) {
    for (unsigned i = 0; i < sizeof offsets / sizeof offsets[0]; i++)
        eepromBuffer.buffer[offsets[i]] = 0x55;
}
void seed_old_version(void) { stored.eeprom_version = EEPROM_VERSION - 1; }
'''
        cfile = folder / "settings.c"
        cfile.write_text(harness)
        cls.targets = {}
        for target in ("SKYSTARS_AM60_V2_F421", "SKYSTARS_KO60_F421"):
            library = folder / (target + ".so")
            subprocess.run(
                shlex.split(os.environ.get("CC", "cc"))
                + ["-std=c11", "-Wall", "-Wextra", "-Werror", "-shared", "-fPIC",
                   "-I", str(folder), "-D" + target, str(cfile), "-o", str(library)],
                check=True,
            )
            cls.targets[target] = ctypes.CDLL(str(library))
        cls.product = cls.targets["SKYSTARS_AM60_V2_F421"]
        cls.other = cls.targets["SKYSTARS_KO60_F421"]

    def setUp(self):
        self.product.seed()
        self.other.seed()

    def assert_policy(self):
        for i, expected in enumerate((0, 1, 125, 125, 126, 3, 1)):
            offset = self.product.policy_offset(i)
            self.assertEqual(self.product.read_byte(offset), expected)
            self.assertEqual(self.product.stored_byte(offset), expected)

    def test_current_eeprom_is_normalized_and_saved_once(self):
        self.product.boot()
        self.assert_policy()
        self.assertEqual(self.product.write_count(), 1)
        self.product.boot()
        self.assert_policy()
        self.assertEqual(self.product.write_count(), 1)

    def test_unrelated_settings_are_preserved_byte_for_byte(self):
        before = [self.product.read_byte(i) for i in range(192)]
        allowed = {self.product.policy_offset(i) for i in range(7)}
        self.product.boot()
        for i, expected in enumerate(before):
            if i not in allowed:
                self.assertEqual(self.product.read_byte(i), expected, i)

    def test_later_save_cannot_persist_incompatible_input_settings(self):
        self.product.boot()
        self.product.disturb_policy()
        self.product.saveEEpromSettings()
        self.assert_policy()
        self.product.boot()
        self.assertEqual(self.product.write_count(), 2)

    def test_existing_version_migration_also_applies_product_policy(self):
        self.product.seed_old_version()
        self.product.boot()
        self.assert_policy()
        self.assertEqual(self.product.write_count(), 1)
        self.product.boot()
        self.assertEqual(self.product.write_count(), 1)

    def test_other_target_keeps_its_saved_input_configuration(self):
        before = [self.other.read_byte(i) for i in range(192)]
        self.other.boot()
        self.assertEqual([self.other.read_byte(i) for i in range(192)], before)
        self.assertEqual(self.other.write_count(), 0)
        self.other.saveEEpromSettings()
        self.assertEqual([self.other.stored_byte(i) for i in range(192)], before)


if __name__ == "__main__":
    unittest.main(verbosity=2)

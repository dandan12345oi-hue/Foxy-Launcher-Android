#!/usr/bin/env python3
"""Regression tests for the Foxy Launcher nixport settings contract."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ENTRY = ROOT / "packaging" / "arm-linux" / "entry_main.py"


class FoxyLauncherSchemaTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.ini = Path(self.temp.name) / "spartanport.ini"
        self.ini.write_text("", encoding="utf-8")

    def tearDown(self):
        self.temp.cleanup()

    def command(self, *args):
        result = subprocess.run(
            [sys.executable, str(ENTRY), "config", args[0], str(self.ini), *args[1:]],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return json.loads(result.stdout)

    def schema(self):
        return self.command("schema")

    def test_mobile_schema_exposes_real_graphics_and_performance_options(self):
        schema = self.schema()
        groups = {group["id"]: group for group in schema["groups"]}
        self.assertIn("display", groups)
        self.assertIn("performance", groups)
        self.assertIn("monitor", groups)
        self.assertIn("quality", groups)
        items = {
            item["key"]: item
            for group in schema["groups"]
            for item in group["items"]
        }
        expected = {
            "render_resolution", "fps_limit", "engine_fps", "frames_queued", "vsync",
            "experimental_upscaler", "upscaler", "preset", "frame_generation",
            "texture_quality", "anisotropy", "shadows", "bloom", "motion_blur",
            "depth_of_field", "rcas", "rcas_strength", "deferred_readback",
            "stale_readback", "async_shaders", "readback_linear",
            "show_fps", "overlay_fps", "overlay_frametime", "overlay_upscaler",
            "overlay_gpu", "overlay_cpu", "overlay_ram", "overlay_vram",
            "overlay_scale", "overlay_corner", "overlay_opacity", "overlay_layout",
        }
        self.assertTrue(expected.issubset(items))
        self.assertEqual(items["render_resolution"]["default"], "720p")
        self.assertEqual(items["fps_limit"]["default"], "60")
        self.assertEqual(items["experimental_upscaler"]["default"], False)
        self.assertEqual(items["upscaler"]["enum"], ["off", "fsr3", "taa"])

    def test_set_get_round_trip_and_numeric_clamp(self):
        payload = {
            "render_resolution": "900p",
            "fps_limit": "60",
            "engine_fps": "120",
            "frames_queued": "2",
            "experimental_upscaler": True,
            "upscaler": "fsr3",
            "preset": "2",
            "frame_generation": "off",
            "texture_quality": "2",
            "rcas_strength": 140,
            "show_fps": True,
            "overlay_gpu": True,
            "overlay_scale": 360,
            "overlay_corner": "3",
            "overlay_opacity": 72,
            "overlay_layout": "1",
        }
        saved = self.command("set", json.dumps(payload))
        self.assertTrue(saved["ok"])
        self.assertEqual(saved["values"]["render_resolution"], "900p")
        self.assertEqual(saved["values"]["fps_limit"], "60")
        self.assertEqual(saved["values"]["engine_fps"], "120")
        self.assertTrue(saved["values"]["experimental_upscaler"])
        self.assertEqual(saved["values"]["upscaler"], "fsr3")
        self.assertEqual(saved["values"]["rcas_strength"], 100)
        self.assertTrue(saved["values"]["show_fps"])
        self.assertTrue(saved["values"]["overlay_gpu"])
        self.assertEqual(saved["values"]["overlay_scale"], 300)
        self.assertEqual(saved["values"]["overlay_corner"], "3")
        self.assertEqual(saved["values"]["overlay_opacity"], 72)
        self.assertEqual(saved["values"]["overlay_layout"], "1")
        current = self.command("get")
        self.assertEqual(current["upscaler"], "fsr3")
        self.assertTrue(current["overlay_gpu"])

    def test_invalid_enum_is_rejected(self):
        result = subprocess.run(
            [sys.executable, str(ENTRY), "config", "set", str(self.ini), json.dumps({"fps_limit": "75"})],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("not in enum", result.stderr)

    def test_manifest_uses_foxy_display_name_without_changing_compatibility_id(self):
        manifest = json.loads((ROOT / "packaging" / "arm-linux" / "port.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["name"], "Foxy Launcher")
        self.assertEqual(manifest["id"], "spartanport")
        self.assertEqual(manifest["entries"][0]["name"], "Foxy Launcher")
        self.assertEqual(manifest["appimage"], "SpartanPort-arm64.AppImage")


if __name__ == "__main__":
    unittest.main()

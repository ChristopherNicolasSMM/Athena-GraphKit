import unittest
from pathlib import Path
from athena_cairo import load_cairosvg, CairoUnavailable

class TestCairoLoader(unittest.TestCase):
    def test_missing_native_dll_does_not_break_module_import(self):
        import athena_cairo
        self.assertTrue(callable(athena_cairo.load_cairosvg))
    def test_vendor_path_exists(self):
        self.assertTrue((Path(__file__).resolve().parents[1] / 'libs' / 'cairo' / 'bin').is_dir())

if __name__ == '__main__': unittest.main()

from unittest import TestCase

from caen import Caen


class TestCaen(TestCase):
    """
    Class for testing caen power supply command formatting
    """
    caen_test_runner = Caen()

    def test_check_return_status(self):
        self.assertTrue(self.caen_test_runner.check_return_status("brd:cmd:ok"))

    def test_setup_channel(self):
        self.assertIn("19", self.caen_test_runner.setup_channel(1, 19))
        self.assertIn("1", self.caen_test_runner.setup_channel("1", "19"))

    def test_set_output(self):
        self.assertIn("20", self.caen_test_runner.set_output(0, "20"))

    def test_enable_output(self):
        self.assertTrue("ON", self.caen_test_runner.enable_output(2, True))
        self.assertTrue("OFF", self.caen_test_runner.enable_output(2, enable=False))

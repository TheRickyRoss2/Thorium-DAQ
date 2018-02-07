from unittest import TestCase
from caen import Caen

class TestCaen(TestCase):
    """
    Class for testing caen power supply command formatting
    """
    caen_test_runner = Caen()

    def test_check_return_status(self):
        self.caen_test_runner.check_return_status("ok")

    def test_setup_channel(self):
        self.caen_test_runner.setup_channel(1, 19)
        self.assertEquals()
        self.fail()

    def test_set_output(self):
        self.fail()

    def test_enable_output(self):
        self.fail()

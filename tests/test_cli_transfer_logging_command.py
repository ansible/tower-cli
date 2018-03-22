from tower_cli.cli.transfer.logging_command import LoggingCommand

from six.moves import StringIO
import sys
import click
from tests.compat import unittest, mock


class LoggingCommandTests(unittest.TestCase):
    """A set of tests to establish that the LoggingCommand metaclass works
    in the way we expect.
    """

    def setUp(self):
        self.held, sys.stdout = sys.stdout, StringIO()

    def clear_string_buffer(self):
        sys.stdout.seek(0)
        sys.stdout.truncate(0)

    def test_print_recap(self):
        with mock.patch.object(click, 'get_terminal_size') as mock_method:
            mock_method.return_value = [80, 128]
            my_logging_command = LoggingCommand()

            # Test default play recap (no starting new line)
            my_logging_command.print_recap()
            recap_msg = "PLAY RECAP *********************************************************************\n" +\
                        "    ok=0    changed=0    warnings=0    failed=0\n\n"
            self.assertEquals(sys.stdout.getvalue(), recap_msg, "First recap message failed")

            # Test second play recap (has starting new line)
            self.clear_string_buffer()
            my_logging_command.print_recap()
            recap_msg = "\nPLAY RECAP *********************************************************************\n" +\
                        "    ok=0    changed=0    warnings=0    failed=0\n\n"
            self.assertEquals(sys.stdout.getvalue(), recap_msg, "Second recap message failed")

            # Test play recap with 1 ok
            self.clear_string_buffer()
            my_logging_command.ok_messages = 1
            my_logging_command.print_recap()
            recap_msg = "\nPLAY RECAP *********************************************************************\n" +\
                        "    ok=1    changed=0    warnings=0    failed=0\n\n"
            self.assertEquals(sys.stdout.getvalue(), recap_msg, "OK recap message failed")

            # Test play recap with 1 changed
            self.clear_string_buffer()
            my_logging_command.changed_messages = 1
            my_logging_command.print_recap()
            recap_msg = "\nPLAY RECAP *********************************************************************\n" +\
                        "    ok=1    changed=1    warnings=0    failed=0\n\n"
            self.assertEquals(sys.stdout.getvalue(), recap_msg, "Changed recap message failed")

            # Test play recap with 1 warnings
            self.clear_string_buffer()
            my_logging_command.warn_messages = 1
            my_logging_command.print_recap()
            recap_msg = "\nPLAY RECAP *********************************************************************\n" +\
                        "    ok=1    changed=1    warnings=1    failed=0\n\n"
            self.assertEquals(sys.stdout.getvalue(), recap_msg, "Warn recap message failed")

            # Test play recap with 1 failed
            self.clear_string_buffer()
            my_logging_command.error_messages = 1
            my_logging_command.print_recap()
            recap_msg = "\nPLAY RECAP *********************************************************************\n" +\
                        "    ok=1    changed=1    warnings=1    failed=1\n\n"
            self.assertEquals(sys.stdout.getvalue(), recap_msg, "Error recap message failed")

    def test_my_print_no_color(self):
        # Validate that with no_color specified a message comes out straight
        my_logging_command = LoggingCommand()
        my_logging_command.no_color = True
        my_logging_command.my_print("Test Message", fg="red", bold="True", nl="False")
        self.assertEquals(sys.stdout.getvalue(), "Test Message\n", "Message with no color did not come out correctly")

    def test_print_into(self):
        # Validate that the intro just prints a blank line
        my_logging_command = LoggingCommand()
        my_logging_command.print_intro()
        self.assertEquals(sys.stdout.getvalue(), "\n", "Print Intro does not print a new line")

    def test_get_terminal_size(self):
        with mock.patch.object(click, 'get_terminal_size') as mock_method:
            mock_method.return_value = [80, 128]
            my_logging_command = LoggingCommand()
            my_logging_command.get_rows()
            self.assertEquals(my_logging_command.columns, 80, "Did not correctly get back the terminal size")

    def test_print_header_row(self):
        with mock.patch.object(click, 'get_terminal_size') as mock_method:
            mock_method.return_value = [80, 128]
            my_logging_command = LoggingCommand()
            my_logging_command.print_header_row("inventory", "test inventory")
            first_inv_msg = "INVENTORY [test inventory] *****************************************************\n"
            self.assertEquals(sys.stdout.getvalue(), first_inv_msg, "First header row incorrect")
            self.clear_string_buffer()
            my_logging_command.print_header_row("inventory", "test inventory")
            second_inv_msg = "\nINVENTORY [test inventory] *****************************************************\n"
            self.assertEquals(sys.stdout.getvalue(), second_inv_msg, "Second header row incorrect")

    def test_log_error(self):
        my_logging_command = LoggingCommand()
        my_logging_command.log_error("TestError")
        self.assertEquals(sys.stdout.getvalue(), "TestError\n", "Error did not come out correctly")
        self.assertEquals(my_logging_command.error_messages, 1)

    def test_log_warn(self):
        my_logging_command = LoggingCommand()
        my_logging_command.log_warn("TestWarn")
        self.assertEquals(sys.stdout.getvalue(), " [WARNING]: TestWarn\n", "Warn did not come out correctly")
        self.assertEquals(my_logging_command.warn_messages, 1)

    def test_log_ok(self):
        my_logging_command = LoggingCommand()
        my_logging_command.log_ok("TestOK")
        self.assertEquals(sys.stdout.getvalue(), "TestOK\n", "OK did not come out correctly")
        self.assertEquals(my_logging_command.ok_messages, 1)

    def test_log_change(self):
        my_logging_command = LoggingCommand()
        my_logging_command.log_change("TestChange")
        self.assertEquals(sys.stdout.getvalue(), "TestChange\n", "Change did not come out correctly")
        self.assertEquals(my_logging_command.changed_messages, 1)

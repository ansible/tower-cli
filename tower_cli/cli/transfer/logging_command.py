from tower_cli.utils import secho
import click
import six


class LoggingCommand:
    ok_messages = 0
    error_messages = 0
    changed_messages = 0
    warn_messages = 0
    columns = None
    no_color = False

    def print_intro(self):
        self.my_print("")

    def get_rows(self):
        self.columns = click.get_terminal_size()[0]

    def print_header_row(self, asset_type, asset_name):
        if self.columns is None:
            self.get_rows()
        else:
            self.my_print('')

        # The 4 is from 2 spaces and 2 brackets
        stars = '*' * (int(self.columns) - (len(asset_type + asset_name) + 4))
        self.my_print(six.text_type("{} [{}] {}").format(
            asset_type.replace("_", " ").upper(), asset_name, stars)
        )

    def print_recap(self):
        if self.columns is None:
            self.get_rows()
        else:
            self.my_print('')

        # Print the recap message
        recap_message = "PLAY RECAP"
        stars = '*' * (int(self.columns) - (len(recap_message) + 1))
        self.my_print("{} {}".format(recap_message, stars))

        spaces_separating_messages = "    "

        # Print OK count
        self.my_print(spaces_separating_messages, nl=False)
        ok = "ok={}".format(self.ok_messages)
        color = ''
        if self.ok_messages > 0:
            color = 'green'
        self.my_print(ok, fg=color, nl=False)

        # Print CHANGED count
        self.my_print(spaces_separating_messages, nl=False)
        changed = "changed={}".format(self.changed_messages)
        color = ''
        if self.changed_messages > 0:
            color = 'yellow'
        self.my_print(changed, fg=color, nl=False)

        # Print WARNING count
        self.my_print(spaces_separating_messages, nl=False)
        warnings = "warnings={}".format(self.warn_messages)
        color = ''
        if self.warn_messages > 0:
            color = 'magenta'
        self.my_print(warnings, fg=color, nl=False)

        # Print ERROR count
        self.my_print(spaces_separating_messages, nl=False)
        error = "failed={}".format(self.error_messages)
        color = ''
        if self.error_messages > 0:
            color = 'red'
        self.my_print(error, fg=color)

        self.my_print("")

    def log_warn(self, warn_message):
        self.my_print(" [WARNING]: {}".format(warn_message), fg='magenta', bold=True)
        self.warn_messages = self.warn_messages + 1

    def log_ok(self, ok_message):
        self.my_print("{}".format(ok_message), fg='green')
        self.ok_messages = self.ok_messages + 1

    def log_change(self, change_message):
        self.my_print("{}".format(change_message), fg='yellow')
        self.changed_messages = self.changed_messages + 1

    def log_error(self, error_message):
        self.my_print("{}".format(error_message), fg='red', bold=True)
        self.error_messages = self.error_messages + 1

    def my_print(self, message=None, fg='', bold=False, nl=True):
        if self.no_color:
            secho(message, fg='', bold=False, nl=nl)
        else:
            secho(message, fg=fg, bold=bold, nl=nl)

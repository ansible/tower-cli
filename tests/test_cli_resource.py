import json
import yaml

import click

from tower_cli import models, resources
from tower_cli.cli.resource import ResSubcommand
from tower_cli.conf import settings

from tests.compat import unittest, mock


class SubcommandTests(unittest.TestCase):
    """A set of tests for establishing that the Subcommand class created
    on the basis of a Reosurce class works in the way we expect.
    """
    def setUp(self):
        """Install a resource instance sufficient for testing common
        things with subcommands.
        """
        class BasicResource(models.Resource):
            endpoint = '/basic/'
            name = models.Field(unique=True)
        self.resource = BasicResource()
        self.command = ResSubcommand(self.resource)

    def test_command_instance(self):
        """Establish that the command based on a resource is, in fact, a
        click MultiCommand.
        """
        # Assert that it is a click command, and that it has the commands
        # available on the resource.
        self.assertIsInstance(self.command, click.MultiCommand)

    def test_list_commands(self):
        """Establish that the `list_commands` method for the command
        corresponds to the commands available on the resource.
        """
        self.assertEqual(set(self.resource.commands),
                         set(self.command.list_commands(None)))

    def test_get_command(self):
        """Establish that the `get_command` method returns the appropriate
        resource method wrapped as a click command.
        """
        list_command = self.command.get_command(None, 'list')

        # Ensure that this is a click command.
        self.assertIsInstance(list_command, click.core.Command)

        # Ensure that this command has an option corresponding to the
        # "name" unique field.
        self.assertEqual(list_command.params[0].name, 'name')
        self.assertIn('--name', list_command.params[0].opts)

    def test_get_command_error(self):
        """Establish that if `get_command` is called against a command that
        does not actually exist on the resource, that null value is returned.
        """
        self.assertEqual(self.command.get_command(None, 'bogus'), None)

    def test_command_with_pk(self):
        """Establish that the `get_command` method appropriately adds a
        primary key argument if the method has a "pk" positional argument.
        """
        # Create a resource with an appropriate command.
        class PKResource(models.BaseResource):
            endpoint = '/pkr/'

            @resources.command
            def my_method(self, pk):
                pass

        # Get the command version of my_method.
        my_method = ResSubcommand(PKResource()).get_command(None, 'my_method')

        # Establish that the `my_method` command does, in fact, have a PK
        # click argument attached.
        self.assertEqual(my_method.params[-1].name, 'pk')

    def test_use_fields_as_options_false(self):
        """Establish that the `use_fields_as_options` attribute is honored
        if set to False.
        """
        # Create a resource with a command that doesn't expect its
        # fields to become options.
        class NoOptResource(models.BaseResource):
            endpoint = '/nor/'

            f1 = models.Field()
            f2 = models.Field()

            @resources.command(use_fields_as_options=False)
            def noopt(self):
                pass

        # Make the resource into a command, and get the noopt subcommand.
        noopt = ResSubcommand(NoOptResource()).get_command(None, 'noopt')

        # Establish that the noopt command does NOT have fields as options.
        self.assertFalse(any([o.name == 'f1' for o in noopt.params]))
        self.assertFalse(any([o.name == 'f2' for o in noopt.params]))

    def test_use_fields_as_options_enumerated(self):
        """Establish that the `use_fields_as_options` attribute is honored
        if set to a tuple containing a subset of fields.
        """
        # Create a resource with a command that doesn't expect its
        # fields to become options.
        class NoOptResource(models.BaseResource):
            endpoint = '/nor/'

            f1 = models.Field()
            f2 = models.Field()

            @resources.command(use_fields_as_options=('f2',))
            def noopt(self):
                pass

        # Make the resource into a command, and get the noopt subcommand.
        noopt = ResSubcommand(NoOptResource()).get_command(None, 'noopt')

        # Establish that the noopt command does NOT have fields as options.
        self.assertFalse(any([o.name == 'f1' for o in noopt.params]))
        self.assertTrue(any([o.name == 'f2' for o in noopt.params]))

    def test_fields_not_options(self):
        """Establish that a field which is not an option is not made into
        an option for commands.
        """
        # Create a resource with a field that is an option and another
        # field that isn't.
        class NoOptionResource(models.Resource):
            endpoint = '/nor/'

            yes = models.Field()
            no = models.Field(is_option=False)

        # Make the resource into a command, and get a reasonably-arbitrary
        # subcommand.
        cmd = ResSubcommand(NoOptionResource()).get_command(None, 'list')

        # Establish that "yes" is an option on the command and "no" is not.
        self.assertTrue(any([o.name == 'yes' for o in cmd.params]))
        self.assertFalse(any([o.name == 'no' for o in cmd.params]))

    def test_field_explicit_key(self):
        """Establish that if a field is given an explicit key, that they
        key is used for the field name instead of the implicit name.
        """
        # Create a resource with a field that has an explicit key.
        class ExplicitKeyResource(models.Resource):
            endpoint = '/ekr/'

            option_name = models.Field('internal_name')

        # Make the resource into a command, and get a reasonably-arbitrary
        # subcommand.
        cmd = ResSubcommand(ExplicitKeyResource()).get_command(None, 'get')

        # Establish that the field has an option of --option-name, and
        # a name of internal_name.
        opt = cmd.params[0]
        self.assertEqual(opt.name, 'internal_name')
        self.assertEqual(opt.opts, ['--option-name'])

    def test_field_help_text_has_prefix(self):
        """Establish that resource field help text is properly prefixed.
        """
        class FieldHelpTextResource(models.Resource):
            endpoint = '/foobar/'

            option_name = models.Field('internal_name', help_text='foobar', required=False)

        cmd = ResSubcommand(FieldHelpTextResource()).get_command(None, 'get')

        opt = cmd.params[0]
        self.assertEqual(opt.help, '[FIELD]foobar')

    def test_docstring_replacement_an(self):
        """Establish that for resources with names beginning with vowels,
        that the automatic docstring replacement is gramatically correct.
        """
        # Create a resource with an approriate name.
        class Oreo(models.Resource):
            resource_name = 'Oreo cookie'   # COOOOOOKIES!!!!
            endpoint = '/oreo/'

        # Get the Oreo resource's create method.
        create = ResSubcommand(Oreo()).get_command(None, 'create')
        self.assertIn('Create an Oreo cookie', create.help)

    def test_docstring_replacement_y(self):
        """Establish that for resources with names ending in y, that plural
        replacement is correct.
        """
        # Create a resource with an approriate name.
        class Oreo(models.Resource):
            resource_name = 'telephony'
            endpoint = '/telephonies/'

        # Get the Oreo resource's create method.
        create = ResSubcommand(Oreo()).get_command(None, 'list')
        self.assertIn('list of telephonies', create.help)

    def test_echo_method(self):
        """Establish that the _echo_method subcommand class works in the
        way we expect.
        """
        func = self.command._echo_method(lambda: {'foo': 'bar'})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='json'):
                func()
            secho.assert_called_once_with(json.dumps({'foo': 'bar'}, indent=2))

    def test_echo_method_changed_false(self):
        """Establish that the _echo_method subcommand decorator works
        in the way we expect if we get an unchanged designation.
        """
        func = self.command._echo_method(lambda: {'changed': False})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='json', color=True):
                func()
            answer = json.dumps({'changed': False}, indent=2)
            secho.assert_called_once_with(answer, fg='green')

    def test_echo_method_changed_true(self):
        """Establish that the _echo_method subcommand decorator works
        in the way we expect if we get an changed designation.
        """
        func = self.command._echo_method(lambda: {'changed': True})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='json', color=True):
                func()
            answer = json.dumps({'changed': True}, indent=2)
            secho.assert_called_once_with(answer, fg='yellow')

    def test_echo_method_yaml_formatted(self):
        """Establish that the `_echo_method` properly returns YAML formatting
        when it gets back a list of objects.
        """
        func = self.command._echo_method(lambda: {'foo': 'bar'})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='yaml'):
                func()
            secho.assert_called_once_with(yaml.safe_dump({'foo': 'bar'},
                                          indent=2,
                                          allow_unicode=True,
                                          default_flow_style=False))

    def test_echo_method_human_formatted(self):
        """Establish that the `_echo_method` properly returns human formatting
        when it gets back a list of objects.
        """
        func = self.command._echo_method(lambda: {'results': [
            {'id': 1, 'name': 'Durham, NC'},
            {'id': 2, 'name': 'Austin, TX'},
        ]})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('1 Durham, NC', output)
        self.assertIn('2 Austin, TX', output)

    def test_echo_method_human_formatted_changed(self):
        """Establish that if there is a change and no id is returned,
        we print a generic OK message.
        """
        func = self.command._echo_method(lambda: {'changed': False})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertEqual(output, 'OK. (changed: false)')

    def test_echo_method_human_formatted_no_records(self):
        """Establish that if there are no records sent to the human formatter,
        that it prints a terse message to that effect.
        """
        func = self.command._echo_method(lambda: {'results': []})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertEqual(output, 'No records found.')

    def test_echo_method_human_formatted_single_result(self):
        """Establish that a single result sent to the human formatter
        shows a table with a single row as expected.
        """
        f = self.command._echo_method(lambda: {'id': 1, 'name': 'Durham, NC'})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                f()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('1 Durham, NC', output)

    def test_echo_method_human_boolean_formatting(self):
        """Establish that booleans are formatted right-aligned, lower-cased
        in human output.
        """
        func = self.command._echo_method(lambda: {'results': [
            {'id': 1, 'name': 'Durham, NC'},
            {'id': 2, 'name': True},
        ]})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('1 Durham, NC', output)
        self.assertIn('2       true', output)

    def test_echo_method_human_pagination(self):
        """Establish that pagination works in human formatting, and it
        prints the way we expect.
        """
        func = self.command._echo_method(lambda: {'results': [
            {'id': 1, 'name': 'Durham, NC'},
            {'id': 2, 'name': True},
        ], 'next': 3, 'count': 10, 'previous': 1})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('(Page 2 of 5.)', output)

    def test_echo_method_human_pagination_last_page(self):
        """Establish that pagination works in human formatting, and it
        prints the way we expect on the final page..
        """
        func = self.command._echo_method(lambda: {'results': [
            {'id': 1, 'name': 'Durham, NC'},
        ], 'next': None, 'count': 3, 'previous': 1})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('(Page 2 of 2.)', output)

    def test_echo_method_human_custom_output(self):
        """Establish that a custom dictionary with no ID is made into a
        table and printed as expected.
        """
        func = self.command._echo_method(lambda:
                                         {'foo': 'bar', 'spam': 'eggs'})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='human'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertIn('foo', output)
        self.assertIn('spam', output)
        self.assertIn('bar', output)
        self.assertIn('eggs', output)

    def test_echo_id(self):
        func = self.command._echo_method(lambda: {'id': 5})
        with mock.patch.object(click, 'secho') as secho:
            with settings.runtime_values(format='id'):
                func()
            output = secho.mock_calls[-1][1][0]
        self.assertEqual('5', output)

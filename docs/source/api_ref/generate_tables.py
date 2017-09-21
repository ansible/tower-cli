import os
import click
from tower_cli import get_resource
from tower_cli.cli import types
from collections import OrderedDict


try:
    unicode
except NameError:
    unicode = str
    basestring = str


ATTR_TO_SHOW = [
    'name',
    'type',
    'help_text',
    'read_only',
    'unique',
    'filterable',
    'required',
]

CLI_TYPE_MAPPING = {
    unicode: 'String',
    str: 'String',
    types.Related: (lambda x: 'Resource ' + str(getattr(x, 'resource_name', 'unknown'))),
    click.Choice: (lambda x: 'Choices: ' + ','.join(getattr(x, 'choices', [])))
}


def convert_type(attr_val):
    if attr_val in CLI_TYPE_MAPPING:
        return CLI_TYPE_MAPPING[attr_val] \
                if isinstance(CLI_TYPE_MAPPING[attr_val], str) \
                else CLI_TYPE_MAPPING[attr_val](attr_val)
    elif type(attr_val) in CLI_TYPE_MAPPING:
        return CLI_TYPE_MAPPING[type(attr_val)] \
                if isinstance(CLI_TYPE_MAPPING[type(attr_val)], str) \
                else CLI_TYPE_MAPPING[type(attr_val)](attr_val)
    try:
        return attr_val.__name__
    except Exception:
        return str(attr_val)


def convert_to_str(field, attr, attr_val):
    if attr == 'help_text' and not attr_val:
        return 'The %s field.' % field.name
    elif attr == 'type':
        return convert_type(attr_val)
    elif not isinstance(attr_val, basestring):
        if attr_val in (True, False, None):
            return str(attr_val)
        else:
            return 'TODO'
    return attr_val


def get_content(res_name):
    res = get_resource(res_name)
    content = OrderedDict()
    for field in res.fields:
        for attr in ATTR_TO_SHOW:
            content.setdefault(attr, [])
            attr_val = getattr(field, attr, 'N/A')
            attr_val = convert_to_str(field, attr, attr_val)
            content[attr].append(attr_val)
    return content


def render_table(content):
    delimiter = ['+']
    titles = ['|']
    values = []
    for attr_name in content:
        column_len = max(len(attr_name), max([len(x) for x in content[attr_name]])) + 1
        delimiter.append('-' * column_len + '+')
        titles.append(attr_name + ' ' * (column_len - len(attr_name)) + '|')
        for i in range(len(content[attr_name])):
            val = content[attr_name][i]
            if len(values) <= i:
                values.append(['|'])
            values[i].append(val + ' ' * (column_len - len(val)) + '|')
    delimiter = ''.join(delimiter)
    titles = ''.join(titles)
    values = [''.join(x) for x in values]
    table = [delimiter]
    table.append(titles)
    table.append(delimiter.replace('-', '='))
    for val in values:
        table.append(val)
        table.append(delimiter)
    return '\n' + '\n'.join(table) + '\n\n'


def insert_table(rst_path, table):
    insert_checkpnt = '.. <table goes here>\n'
    with open(rst_path) as f:
        file_content = f.read()
        start = file_content.find(insert_checkpnt) + len(insert_checkpnt)
        end = file_content.rfind(insert_checkpnt)
    if start >= 0 and end >= 0:
        with open(rst_path, 'w') as f:
            f.write(file_content[: start] + table + file_content[end:])


def process_resource(res_name, rst_path):
    content = get_content(res_name)
    table = render_table(content)
    insert_table(rst_path, table)


def main():
    for root, dirs, files in os.walk('resources/'):
        for file_ in files:
            if not file_.endswith('.rst'):
                continue
            process_resource(file_[: -len('.rst')], os.path.join(root, file_))


if __name__ == '__main__':
    main()

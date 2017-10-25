import os


API_VERSION = 1
package_name = 'tower_cli_v%s' % API_VERSION


def convert_file(filename):
    with open(filename) as f:
        s = f.read()
    if package_name in s:
        raise Exception(
            'While attempting to convert %s. '
            'Command has already ran, no need to run again.' % filename
        )
    s = s.replace('tower_cli', package_name)
    s = s.replace('tower-cli', 'tower-cli-v%s' % API_VERSION)
    with open(filename, "w") as f:
        f.write(s)


for dname, dirs, files in os.walk(package_name):
    for fname in files:
        fpath = os.path.join(dname, fname)
        convert_file(fpath)


convert_file('setup_v%s.py' % API_VERSION)

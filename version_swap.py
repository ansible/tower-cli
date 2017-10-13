import os


API_VERSION = 2
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
    with open(filename, "w") as f:
        f.write(s)


# Conversion of secondary source tree
for dname, dirs, files in os.walk(package_name):
    for fname in files:
        fpath = os.path.join(dname, fname)
        convert_file(fpath)


# Conversion of seconary setup file
convert_file('setup_v%s.py' % API_VERSION)

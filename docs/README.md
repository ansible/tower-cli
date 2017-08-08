This README documentation walks you through the process of generating a local doc site for Tower CLI.

Before the actual generating process, make sure you have cloned Tower CLI from github and checked out the right
version tag you want to generate docs from. Also, we use [graphviz](http://www.graphviz.org/) for some graph
generations in doc. Make sure to install graphviz. For example, on OS X:
```
$ brew install graphviz
```
It is always suggested you generate docs in a python virtual environment to prevent any dependency conflicts.
```
$ virtualenv docs
```
And
```
source docs/bin/activate
```
to activate the virtual environment.

In the newly created empty virtual environment, install [sphinx](http://www.sphinx-doc.org/en/stable/), our doc
generating engine.
```
$ sudo pip install sphinx
```
Sphinx walks through an existing python package's source code tree to generate its documentation. so make sure tower
CLI is installed also.
```
$ cd <tower-cli's repo>
$ make install
```
Then, under `docs/` directory, `mkdir build` to create the subdirectory for hosting the local doc site. Also, under
`docs/source`, `mkdir _static` and `mkdir _templates` which are necessary placeholders for doc site compilation.

In Tower CLI, each resource has a lot of fields that need to be grouped and documented as `.rst`-formatted tables.
we provide a script, `docs/source/api_ref/generate_tables.py`, to auto-generate all tables. In order to run the
script, `cd docs/source/api_ref/` and
```
$ python generate_tables.py
```
Now that all documentation source scripts are ready, navigate to `docs/` directory and generate the doc site by
```
$ make html
```
Finally, in web browser, navigate to `file://<wherever tower-cli's repo is>/docs/build/html/index.html` and see
the site for yourself.

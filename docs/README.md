This README documentation walks you through the process of generating a local
doc site for Tower CLI.

Before the actual generating process, make sure you have cloned Tower CLI from
github and checked out the right version tag you want to generate docs from.
Also, we use [graphviz](http://www.graphviz.org/) for some graph generations in
doc. Make sure to install graphviz. For example, on OS X:

```
$ brew install graphviz
```

It is always suggested you generate docs in a python virtual environment to
prevent any dependency conflicts.  To simplify this process, we use `tox`:

```
$ tox -edocs
```

Once tox finishes, navigate to `file://<wherever tower-cli's repo
is>/docs/build/html/index.html` in a web browser to view the HTML documentation.

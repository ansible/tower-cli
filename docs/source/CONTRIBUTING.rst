Contributor's Guide
===================

All kinds of contributions are more than welcomed. You can help make tower CLI better by reporting bugs, come up
with feature ideas or, even further, help maintainers out by making pull requests. Make sure you follow the rules
below when contributing and you are ready to roll ;)

Bug Reports
-----------

Reporting bugs is highly valuable to us. For flexibility, we do not provide issue templates, but describe the issue
as specific as possible to make it easier and faster for us to hunt down the issue.

- First check existing issues to see if it has already been created, if it has, giving issue description a "thumbs up".
- Mark the issue with 'bug' label.
- Be sure to mention Tower backend version, Tower CLI version and python interpreter version when the bug occurs.
- Copy-paste the detailed usage (code snippet when using as python library and command when using as CLI) and error
  message if possible.

Feature Requests
----------------

We welcome all sorts of feature ideas, but note, it may be scheduled for a future release rather than the next one,
please be patient while we process your request. We will ping you on github once the feature is implemented.

- Mark the issue with 'enhancement' label.

Architecture Overview
---------------------

All available Tower CLI resources descent from abstract class ``tower_cli.models.base.BaseResource``, which provides
two fundamental methods, ``read`` and ``write``. ``read`` wraps around a GET method to the specified resource, while
``write`` wraps around a POST or PATCH on condition. Most public resource APIs, like ``create`` or ``list``, are
essentially using a combination of ``read`` and ``write`` to communicate with Tower REST APIs.

.. autoclass:: tower_cli.models.base.BaseResource
   :members: read, write

Here is the detailed class hierarchy from ``tower_cli.models.base.BaseResource`` to all specific Tower resources:

.. inheritance-diagram:: tower_cli.models.base tower_cli.models.fields tower_cli.resources.ad_hoc tower_cli.resources.credential_type tower_cli.resources.credential tower_cli.resources.group tower_cli.resources.host tower_cli.resources.instance_group tower_cli.resources.instance tower_cli.resources.inventory_script tower_cli.resources.inventory_source tower_cli.resources.inventory_update tower_cli.resources.inventory tower_cli.resources.job_template tower_cli.resources.job tower_cli.resources.label tower_cli.resources.node tower_cli.resources.notification_template tower_cli.resources.organization tower_cli.resources.project tower_cli.resources.project_update tower_cli.resources.role tower_cli.resources.schedule tower_cli.resources.setting tower_cli.resources.team tower_cli.resources.unified_job tower_cli.resources.user tower_cli.resources.workflow_job tower_cli.resources.workflow
   :parts: 0

Details of each Tower CLI resource module are available under ``tower_cli/resources/``.

Some root-level modules under ``tower_cli/`` folder are of great importance. Specifically, ``api.py`` contains details
of the API client Tower CLI used to make HTTP(S) requests using
`requests <http://docs.python-requests.org/en/master/>`_, and ``conf.py`` is used to define and initialize singleton
setting object ``tower_cli.conf.settings``.

On the other hand, ``tower_cli/cli/`` folder contains code that extends tower_cli from a python library into a full-
fledged command-line interface. We use `click <http://click.pocoo.org/5/>`_ as the CLI engine.

.. inheritance-diagram:: tower_cli.cli.action tower_cli.cli.base tower_cli.cli.resource tower_cli.cli.misc tower_cli.cli.types
   :parts: 0

Code Contributions
------------------

Setting up development environment and playing around with Tower CLI is quite straight-forward, here is the usual
development procedure:

1. Branch out a local issue branch from the correct base branch.
2. Create an empty virtual environment.
3. Code.
4. Run ``make install`` to install development Tower CLI and all its dependency to virtual environment.
5. Manually test on your bug fix/feature and modify until manual tests pass.
6. Run ``sudo pip install tox``. Then at the root directory of Tower CLI repository, run ``sudo tox .`` to run flake8
   verify and unit test against all supported python versions. Run and modify until all flake8 checks and
   unit tests pass.
7. Commit, push to local fork and make pull request targeting the correct base branch.
8. Wait for a maintainer to either approve and merge the pull request, or update pull request according to feedback
   comment.

Some points to keep in mind when developing:

- Target the correct branch. Currently we use branch 'v1' to track 3.1.x versions and 'master' to track 3.2.0 and
  beyond.
- Consider all API versions. Currently 3.1.x versions are exclusively used for API v1 and 3.2.0 and beyond are
  exclusively used for API v2, that means if you fixed a bug for 3.1.8, switch to 3.2.0 and see if the same or
  similar bug exists and needs similar fix.
- Consider python 2/3 compatibility, make good use of ``six`` and ``tower_cli.compat``.
- Consider docs update. Whenever a new resource, new resource public method or new resource field is added, inspect
  the docs folder and make all necessary updates before committing. Whenever ``HISTORY.rst`` at base directory changes
  replace ``docs/source/HISTORY.rst`` with the latest version.
- Adhere to the flake8 specifications when developing, the only exception we allow is the maximum line length, which
  is 120 characters rather than 79.
- Be pythonic by using meaningful names and clear structures. Make code self-explanatory rather than adding excessive
  comments.
- Be test-driven. Although not mandatory, please try keeping test coverage at least the same as before, we appreciate
  it if you can increase our test coverage in your pull requests.

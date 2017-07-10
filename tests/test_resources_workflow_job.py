from tower_cli import get_resource
from tower_cli.api import client

from tests.compat import unittest, mock


class WorkflowJobTest(unittest.TestCase):
    def setUp(self):
        self.res = get_resource('workflow_job')

    def test_lookup_stdout(self):
        with client.test_mode as t:
            t.register_json('/unified_jobs/?order_by=finished&status__in=successful%2Cfailed%2Cerror',
                            {'count': 2,
                             'results': [
                                 {'id': 1, 'name': 'Durham, NC'},
                                 {'id': 2, 'name': 'Austin, TX'}
                             ],
                             'next': None, 'previous': None})
            ret = self.res.lookup_stdout()
            self.assertIn('Durham, NC', ret)
            self.assertIn('Austin, TX', ret)
            self.assertEqual(len(ret.split('\n')), 7)

    def test_lookup_stdout_not_full(self):
        with client.test_mode as t:
            t.register_json('/unified_jobs/?order_by=finished&status__in=successful%2Cfailed%2Cerror',
                            {'count': 2,
                             'results': [
                                 {'id': 1, 'name': 'Durham, NC'},
                                 {'id': 2, 'name': 'Austin, TX'}
                             ],
                             'next': None, 'previous': None})
            ret = self.res.lookup_stdout(full=False)
            self.assertIn('Durham, NC', ret)
            self.assertIn('Austin, TX', ret)
            self.assertEqual(len(ret.split('\n')), 6)

    def test_lookup_stdout_start_n_end(self):
        with client.test_mode as t:
            t.register_json('/unified_jobs/?order_by=finished&status__in=successful%2Cfailed%2Cerror',
                            {'count': 2,
                             'results': [
                                 {'id': 1, 'name': 'Durham, NC'},
                                 {'id': 2, 'name': 'Austin, TX'}
                             ],
                             'next': None, 'previous': None})
            ret = self.res.lookup_stdout(start_line=3, end_line=4)
            self.assertIn('Durham, NC', ret)
            self.assertNotIn('Austin, TX', ret)
            self.assertEqual(len(ret.split('\n')), 2)

    def test_launch(self):
        with client.test_mode as t:
            t.register_json('/workflow_job_templates/1/launch/', {'id': 1}, method='POST')
            self.res.launch(workflow_job_template=1)

    def test_launch_monitor(self):
        with client.test_mode as t:
            t.register_json('/workflow_job_templates/1/launch/', {'id': 1}, method='POST')
            with mock.patch.object(self.res, 'monitor', mock.MagicMock()) as m:
                self.res.launch(workflow_job_template=1, monitor=True)
                assert m.called

    def test_launch_wait(self):
        with client.test_mode as t:
            t.register_json('/workflow_job_templates/1/launch/', {'id': 1}, method='POST')
            with mock.patch.object(self.res, 'wait', mock.MagicMock()) as m:
                self.res.launch(workflow_job_template=1, wait=True)
                assert m.called

    def test_get_attribute(self):
        self.res.__getattribute__('summary')
        with self.assertRaises(AttributeError):
            self.res.__getattribute__('stdout')

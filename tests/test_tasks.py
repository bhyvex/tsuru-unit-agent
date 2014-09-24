# -*- coding: utf-8 -*-

from unittest import TestCase
import mock
import os
import sys

from tsuru_unit_agent.tasks import (
    execute_start_script,
    save_apprc_file,
    run_build_hooks,
    load_app_yaml,
    run_restart_hooks,
)


class TestTasks(TestCase):

    @mock.patch("os.environ", {'env': 'var'})
    @mock.patch("subprocess.Popen")
    def test_execute(self, popen_mock):
        wait_mock = popen_mock.return_value.wait
        wait_mock.return_value = 0
        execute_start_script("my_command")
        self.assertEqual(popen_mock.call_args[0][0], 'my_command')
        self.assertEqual(popen_mock.call_args[1]['shell'], True)
        self.assertEqual(popen_mock.call_args[1]['cwd'], '/')
        self.assertDictEqual(popen_mock.call_args[1]['env'], {'env': 'var'})
        wait_mock.assert_called_once()

    @mock.patch("os.environ", {'myenv': 'var'})
    @mock.patch("sys.exit")
    @mock.patch("subprocess.Popen")
    def test_execute_failing(self, popen_mock, exit_mock):
        wait_mock = popen_mock.return_value.wait
        wait_mock.return_value = 10
        execute_start_script("my_command")
        self.assertEqual(popen_mock.call_args[0][0], 'my_command')
        self.assertEqual(popen_mock.call_args[1]['shell'], True)
        self.assertEqual(popen_mock.call_args[1]['cwd'], '/')
        self.assertDictEqual(popen_mock.call_args[1]['env'], {'myenv': 'var'})
        wait_mock.assert_called_once()
        exit_mock.assert_called_once_with(10)

    def test_save_apprc_file(self):
        environs = [
            {"name": "DATABASE_HOST", "value": "localhost", "public": True},
            {"name": "DATABASE_USER", "value": "root", "public": True},
        ]

        with mock.patch("io.open", mock.mock_open()) as m:
            save_apprc_file(environs)
            m.assert_called_once_with("/home/application/apprc", "w")
            write_mock = m().write
            self.assertRegexpMatches(write_mock.mock_calls[0][1][0], '# generated by tsuru at .*\n')
            write_mock.assert_any_call('export DATABASE_HOST="localhost"\n')
            write_mock.assert_any_call('export DATABASE_USER="root"\n')
            self.assertEqual(len(write_mock.mock_calls), 3)


class RunHooksTest(TestCase):
    @mock.patch("os.environ", {'env': 'var'})
    @mock.patch("subprocess.Popen")
    def test_execute_commands(self, popen_call):
        wait_mock = popen_call.return_value.wait
        wait_mock.return_value = 0
        data = {"hooks": {"build": ["ble"]}}
        run_build_hooks(data)
        self.assertEqual(popen_call.call_args[0][0], 'ble')
        self.assertEqual(popen_call.call_args[1]['shell'], True)
        self.assertEqual(popen_call.call_args[1]['cwd'], '/')
        self.assertDictEqual(popen_call.call_args[1]['env'], {'env': 'var'})
        wait_mock.assert_called_once()

    @mock.patch("os.environ", {})
    @mock.patch("os.path.exists")
    @mock.patch("subprocess.Popen")
    def test_execute_commands_default_cwd_exists(self, popen_call, exists_mock):
        wait_mock = popen_call.return_value.wait
        wait_mock.return_value = 0
        exists_mock.return_value = True
        data = {"hooks": {"build": ["ble"]}}
        run_build_hooks(data)
        self.assertEqual(popen_call.call_args[0][0], 'ble')
        self.assertEqual(popen_call.call_args[1]['shell'], True)
        self.assertEqual(popen_call.call_args[1]['cwd'], '/home/application/current')
        self.assertDictEqual(popen_call.call_args[1]['env'], {})
        wait_mock.assert_called_once()
        exists_mock.assert_called_once_with("/home/application/current")

    @mock.patch("os.environ", {})
    @mock.patch("sys.exit")
    @mock.patch("subprocess.Popen")
    def test_execute_failing_commands(self, popen_call, exit_mock):
        wait_mock = popen_call.return_value.wait
        wait_mock.return_value = 5
        data = {"hooks": {"build": ["ble"]}}
        run_build_hooks(data)
        self.assertEqual(popen_call.call_args[0][0], 'ble')
        self.assertEqual(popen_call.call_args[1]['shell'], True)
        self.assertEqual(popen_call.call_args[1]['cwd'], '/')
        self.assertDictEqual(popen_call.call_args[1]['env'], {})
        wait_mock.assert_called_once()
        exit_mock.assert_called_once_with(5)

    @mock.patch("subprocess.Popen")
    def test_execute_commands_hooks_empty(self, subprocess_call):
        data = {}
        run_build_hooks(data)
        subprocess_call.assert_not_called()
        data = {"hooks": None}
        run_build_hooks(data)
        subprocess_call.assert_not_called()
        data = {"hooks": {"build": None}}
        run_build_hooks(data)
        subprocess_call.assert_not_called()
        data = {"hooks": {"build": []}}
        run_build_hooks(data)
        subprocess_call.assert_not_called()


class RunRestartHooksTest(TestCase):
    @mock.patch("os.environ", {'env': 'var'})
    @mock.patch("subprocess.Popen")
    def test_run_restart_hooks(self, popen_call):
        popen_call.return_value.stdout.readline.return_value = ''
        popen_call.return_value.stderr.readline.return_value = ''
        wait_mock = popen_call.return_value.wait
        wait_mock.return_value = 0
        data = {"hooks": {"restart": {
            "before": ["b1"],
            "before-each": ["b2"],
            "after": ["a1"],
            "after-each": ["a2"],
        }}}
        run_restart_hooks('before', data)
        self.assertEqual(popen_call.call_count, 2)
        self.assertEqual(popen_call.call_args_list[0][0][0], 'b2')
        self.assertEqual(popen_call.call_args_list[0][1]['shell'], True)
        self.assertEqual(popen_call.call_args_list[0][1]['cwd'], '/')
        self.assertDictEqual(popen_call.call_args_list[0][1]['env'], {'env': 'var'})
        self.assertEqual(popen_call.call_args_list[1][0][0], 'b1')
        wait_mock.assert_called_once()
        run_restart_hooks('after', data)
        self.assertEqual(popen_call.call_count, 4)
        self.assertEqual(popen_call.call_args_list[3][0][0], 'a1')
        self.assertEqual(popen_call.call_args_list[2][0][0], 'a2')

    @mock.patch("tsuru_unit_agent.tasks.Stream")
    @mock.patch("os.environ", {'env': 'var'})
    @mock.patch("subprocess.Popen")
    def test_run_restart_hooks_calls_stream(self, popen_call, stream_mock):
        out1 = ['stdout_out1', '']
        out2 = ['stderr_out1', '']
        popen_call.return_value.stdout.readline.side_effect = lambda: out1.pop(0)
        popen_call.return_value.stderr.readline.side_effect = lambda: out2.pop(0)
        wait_mock = popen_call.return_value.wait
        wait_mock.return_value = 0
        data = {"hooks": {"restart": {
            "before": ["b1"],
        }}}
        run_restart_hooks('before', data)
        self.assertEqual(popen_call.call_count, 1)
        self.assertEqual(popen_call.call_args_list[0][0][0], 'b1')
        self.assertEqual(popen_call.call_args_list[0][1]['shell'], True)
        self.assertEqual(popen_call.call_args_list[0][1]['cwd'], '/')
        self.assertDictEqual(popen_call.call_args_list[0][1]['env'], {'env': 'var'})
        wait_mock.assert_called_once()
        stream_mock.assert_any_call(echo_output=sys.stdout, default_stream_name='stdout',
                                    watcher_name='unit-agent')
        stream_mock.assert_any_call(echo_output=sys.stderr, default_stream_name='stderr',
                                    watcher_name='unit-agent')
        write_mock = stream_mock.return_value.write
        write_mock.assert_any_call('stdout_out1')
        write_mock.assert_any_call('stderr_out1')


class LoadAppYamlTest(TestCase):
    def setUp(self):
        self.working_dir = os.path.dirname(__file__)
        self.data = '''
hooks:
  build:
    - {0}_1
    - {0}_2'''

    def test_load_app_yaml(self):
        filenames = ["tsuru.yaml", "tsuru.yml", "app.yaml", "app.yml"]
        for name in filenames:
            with open(os.path.join(self.working_dir, name), "w") as f:
                f.write(self.data.format(name))

        for name in filenames:
            data = load_app_yaml(self.working_dir)
            self.assertEqual(data, {"hooks": {"build": ["{}_1".format(name), "{}_2".format(name)]}})
            os.remove(os.path.join(self.working_dir, name))

    def test_load_without_app_files(self):
        data = load_app_yaml(self.working_dir)
        self.assertDictEqual(data, {})

    def test_load_with_empty_yaml(self):
        with open(os.path.join(self.working_dir, "tsuru.yaml"), "w") as f:
            f.write("")
        data = load_app_yaml(self.working_dir)
        self.assertDictEqual(data, {})
        os.remove(os.path.join(self.working_dir, "tsuru.yaml"))

    def test_load_yaml_encoding(self):
        data = load_app_yaml(os.path.join(self.working_dir, "fixtures/iso88591"))
        self.assertDictEqual(data, {"key": "x"})
        data = load_app_yaml(os.path.join(self.working_dir, "fixtures/utf-8"))
        self.assertDictEqual(data, {"key": u"áéíãôüx"})

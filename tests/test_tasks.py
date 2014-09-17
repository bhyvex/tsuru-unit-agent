from unittest import TestCase
import mock
import os

from tsuru_unit_agent.tasks import execute_start_script, save_apprc_file, run_hooks, load_app_yaml


class TestTasks(TestCase):

    @mock.patch("subprocess.Popen")
    def test_execute(self, popen_mock):
        wait_mock = popen_mock.return_value.wait
        wait_mock.return_value = 0
        environs = [
            {"name": "DATABASE_HOST", "value": "localhost", "public": True},
            {"name": "DATABASE_USER", "value": "root", "public": True},
        ]
        execute_start_script("my_command", environs)
        popen_mock.assert_called_with("my_command", shell=False, cwd="/home/application/current", env={
            "DATABASE_HOST": "localhost",
            "DATABASE_USER": "root",
        })
        wait_mock.assert_called_once()

    @mock.patch("sys.exit")
    @mock.patch("subprocess.Popen")
    def test_execute_failing(self, popen_mock, exit_mock):
        wait_mock = popen_mock.return_value.wait
        wait_mock.return_value = 10
        environs = [
            {"name": "DATABASE_HOST", "value": "localhost", "public": True},
            {"name": "DATABASE_USER", "value": "root", "public": True},
        ]
        execute_start_script("my_command", environs)
        popen_mock.assert_called_with("my_command", shell=False, cwd="/home/application/current", env={
            "DATABASE_HOST": "localhost",
            "DATABASE_USER": "root",
        })
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
    @mock.patch("subprocess.Popen")
    def test_execute_commands(self, popen_call):
        wait_mock = popen_call.return_value.wait
        wait_mock.return_value = 0
        data = {"hooks": {"build": ["ble"]}}
        envs = [
            {"name": "my_key", "value": "my_value"},
        ]
        run_hooks(data, envs)
        popen_call.assert_called_with("ble", shell=True,
                                      cwd="/home/application/current", env={'my_key': 'my_value'})
        wait_mock.assert_called_once()

    @mock.patch("sys.exit")
    @mock.patch("subprocess.Popen")
    def test_execute_failing_commands(self, popen_call, exit_mock):
        wait_mock = popen_call.return_value.wait
        wait_mock.return_value = 5
        data = {"hooks": {"build": ["ble"]}}
        envs = [
            {"name": "my_key", "value": "my_value"},
        ]
        run_hooks(data, envs)
        popen_call.assert_called_with("ble", shell=True,
                                      cwd="/home/application/current", env={'my_key': 'my_value'})
        wait_mock.assert_called_once()
        exit_mock.assert_called_once_with(5)

    @mock.patch("subprocess.Popen")
    def test_execute_commands_hooks_empty(self, subprocess_call):
        data = {}
        run_hooks(data, [])
        subprocess_call.assert_not_called()
        data = {"hooks": None}
        run_hooks(data, [])
        subprocess_call.assert_not_called()
        data = {"hooks": {"build": None}}
        run_hooks(data, [])
        subprocess_call.assert_not_called()
        data = {"hooks": {"build": []}}
        run_hooks(data, [])
        subprocess_call.assert_not_called()


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
        self.assertEqual(data, None)

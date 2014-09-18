import subprocess
import io
import os
import yaml
import sys
import os.path

from datetime import datetime


def exec_with_envs(commands, tsuru_envs, with_shell=False, working_dir="/home/application/current"):
    envs = {env['name']: env['value'] for env in tsuru_envs}
    envs.update(os.environ)
    if not os.path.exists(working_dir):
        working_dir = "/"
    for command in commands:
        status = subprocess.Popen(command, shell=with_shell, cwd=working_dir, env=envs).wait()
        if status != 0:
            sys.exit(status)


def execute_start_script(start_cmd, tsuru_envs):
    exec_with_envs([start_cmd], tsuru_envs, with_shell=True)


def run_hooks(app_data, tsuru_envs):
    commands = (app_data.get('hooks') or {}).get('build') or []
    exec_with_envs(commands, tsuru_envs, with_shell=True)


def run_restart_hooks(position, app_data, tsuru_envs):
    restart_hook = (app_data.get('hooks') or {}).get('restart') or {}
    commands = restart_hook.get('{}-each'.format(position)) or []
    commands += restart_hook.get(position) or []
    exec_with_envs(commands, tsuru_envs, with_shell=True)


def load_app_yaml(working_dir="/home/application/current"):
    files_name = ["tsuru.yaml", "tsuru.yml", "app.yaml", "app.yml"]
    for file_name in files_name:
        try:
            with io.open(os.path.join(working_dir, file_name)) as f:
                return yaml.load(f.read())
        except IOError:
            pass
    return None


def save_apprc_file(environs):
    with io.open("/home/application/apprc", "w") as file:
        file.write(u"# generated by tsuru at {}\n".format(datetime.now()))
        for env in environs:
            file.write(u'export {}="{}"\n'.format(env["name"], env["value"]))

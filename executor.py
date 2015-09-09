#!/usr/bin/python
#coding=UTF-8

from subprocess import Popen
import os, pwd, psutil

class Execution():

    def __init__(self, algorithm_executable, algorithm_params, algorithm_dir, project_sandbox_dir, os_username, stdout, stderr):
        """

        """
        assert isinstance(algorithm_executable, basestring)
        assert isinstance(algorithm_params, list)
        assert isinstance(algorithm_dir, basestring)
        assert isinstance(project_sandbox_dir, basestring)
        assert isinstance(os_username, basestring)

        self.algorithm_executable = algorithm_executable
        self.algorithm_params = algorithm_params
        self.algorithm_dir = algorithm_dir
        self.project_sandbox_dir = project_sandbox_dir
        self.os_username = os_username
        self.stdout = stdout
        self.stderr = stderr

def execute(execution):
    """
    Starts a command execution immediately.
    :param execution: Execution class instance
    :return: Process instance from Popen function
    """

    pw_record = pwd.getpwnam(execution.os_username)
    user_name = pw_record.pw_name
    user_home_dir = pw_record.pw_dir
    user_uid = pw_record.pw_uid
    user_gid = pw_record.pw_gid
    env = os.environ.copy()
    env['HOME'] = user_home_dir
    env['LOGNAME'] = user_name
    env['PWD'] = execution.project_sandbox_dir
    env['USER'] = user_name

    executable = execution.algorithm_executable

    if execution.algorithm_params[0].endswith('.ksh'):
        execution.algorithm_params[0] = '/tmp/'+execution.algorithm_params[0]
        with open(execution.algorithm_params[0]+".new", "wt") as fout:
            with open(execution.algorithm_params[0], "rt") as fin:
                for line in fin:
                    fout.write(line.replace('/AzureBlobStorage/', '/tmp/'))
        os.remove(execution.algorithm_params[0])
        os.rename(execution.algorithm_params[0]+".new", execution.algorithm_params[0])
        os.chmod(execution.algorithm_params[0], 0o777)
        logs_path = os.path.join(os.path.dirname(execution.algorithm_params[0]), 'logs')
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)
            os.chmod(logs_path, 0o777)

    params = [executable] + execution.algorithm_params

    p = Popen(cwd=execution.project_sandbox_dir,
              executable=executable,
              args=params,
              preexec_fn=__demote(user_uid, user_gid),
              stdout=execution.stdout,
              stderr=execution.stderr,
              env={"HOME":"/home/"+execution.os_username})

    return p


def __demote(user_uid, user_gid):
    def result():
        os.setgid(user_gid)
        os.setuid(user_uid)
    return result









if __name__ == '__main__':

    f = open("/tmp/out.txt", "w")

    p = execute(Execution(algorithm_dir="/tmp",
                      algorithm_executable="sleep.sh",
                      project_sandbox_dir="/tmp",
                      os_username="daltrogama",
                      stderr=f, stdout=f, algorithm_params=['1']))
    print "Rodando: ", p.pid

    print "Ok? ", p.returncode
    p.wait()
    print "Ok? ", p.returncode

    print "phymem_usage=",psutil.phymem_usage().used
    print psutil.cpu_percent()

    f.close()
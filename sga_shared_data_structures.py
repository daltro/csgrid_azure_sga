#!/usr/bin/python
#  coding=UTF-8

from datetime import datetime

class CommandMetadata:

    def __init__(self,
                 command_id,
                 algorithm_directory,
                 project_prfx,
                 project_input_files,
                 algorithm_executable_name,
                 algorithm_parameters,
                 sent_timestamp,
                 machine_size):

        assert isinstance(command_id, basestring)
        assert isinstance(algorithm_directory, basestring)
        assert isinstance(project_prfx, basestring)
        assert isinstance(project_input_files, list)
        assert isinstance(algorithm_executable_name, basestring)
        assert isinstance(algorithm_parameters, list)
        assert isinstance(sent_timestamp, datetime)
        assert isinstance(machine_size, basestring)

        self.command_id = command_id
        self.algorithm_bin_file = algorithm_directory
        self.project_prfx = project_prfx
        self.project_input_files = project_input_files
        self.algorithm_executable_name = algorithm_executable_name
        self.algorithm_parameters = algorithm_parameters
        self.sent_timestamp = sent_timestamp
        self.machine_size = machine_size


class MachineStatus():

    def __init__(self):
        return
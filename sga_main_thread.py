#!/usr/bin/python
#coding=UTF-8

from daemon import Daemon
from sga_shared_data_structures import CommandMetadata
from SandboxManager import SandboxManager
from subprocess import Popen
import executor
import ConfigParser, imp, socket

import time, random

sga_debug = True

def trace(message):
    if sga_debug:
        print message


class SgaDaemon(Daemon):

    def run(self):

        running_process = None  # Popen()
        execution_metadata = None  # CommandMetadata()
        self.execution_stdout = None

        trace("Lendo configuração...")
        config = ConfigParser.ConfigParser()
        config.read("sga.ini")

        # O nome do usuário do sistema operacional que será usado para executar os algoritmos
        self.os_execution_username = config.get("sga", "os_execution_username")

        # O nome do sga será o nome da máquina
        machine_name = socket.gethostname()
        config.set("sga", "name", machine_name)

        # Carregar o conector
        trace("Carregando conector...")
        connector_module = imp.load_source("connector", config.get("sga", "connector"))
        self.connector = connector_module.create(config)

        self.sandbox_manager = SandboxManager(config, self.connector)

        # Configurações gerais, de polling
        polling_time_secs = config.getfloat("sga", "polling_time_secs")

        try:
            # Loop de eventos principal
            while True:

                # Se não estiver executando nada neste instante,
                # checar por algo para executar agora
                if running_process is None:
                    trace("Checando se há nova tarefa...")
                    execution_metadata = self.__check_new_tasks()
                    if not execution_metadata is None:
                        trace("Tarefa encontrada. Disparando execução...")
                        running_process = self.__start_execution(execution_metadata)
                        if running_process is None:
                            print("Não foi possível executar comando recebido! Abortando este comando.")
                            execution_metadata = None
                    else:
                        trace(" nada para fazer.")
                        self.__shutdown_myself()

                else:
                    if running_process.poll() is not None:
                        # Execução finalizada! Enviar status:
                        trace("Detectado término da execução")
                        self.__end_execution(execution_metadata)
                        execution_metadata = None
                        running_process = None

                    else:
                        # Execução em andamento. Checar se há mensagem de cancelamento:
                        trace("Execução em andamento...")
                        if self.__check_cancel_request(execution_metadata):
                            trace("Cancelamento detectado. Interrompendo processo...")
                            # Execução cancelada!
                            self.__send_status(execution_metadata, "Canceling")
                            self.__cancel_execution(running_process)
                            self.__send_status(execution_metadata, "Canceled")
                        else:
                            # Execução acontecendo normalmente...
                            self.__send_status(execution_metadata, "Running")

                time.sleep(polling_time_secs)

        except KeyboardInterrupt:
            trace("Tchauzinho.")

    def __check_new_tasks(self):
        return self.connector.check_new_tasks()

    def __start_execution(self, execution_metadata):

        self.__send_status(execution_metadata, "Downloading")
        algorithm_dir = self.sandbox_manager.get_algorithm(execution_metadata.algorithm_bin_file)
        project_sandbox_dir = self.sandbox_manager.get_project(project_prfx=execution_metadata.project_prfx,
                                                               project_input_files=execution_metadata.project_input_files)

        if self.execution_stdout is not None:
            self.execution_stdout.close()

        self.execution_stdout = open("/tmp/out.txt", "w")

        self.__send_status(execution_metadata, "Running")
        return executor.execute(executor.Execution(
            algorithm_executable=execution_metadata.algorithm_executable_name,
            algorithm_params=execution_metadata.algorithm_parameters,
            algorithm_dir=algorithm_dir,
            project_sandbox_dir=project_sandbox_dir,
            os_username=self.os_execution_username,
            stdout=self.execution_stdout,
            stderr=self.execution_stdout
        ))

    def __end_execution(self, execution_metadata):
        self.__send_status(execution_metadata, "Uploading")
        self.sandbox_manager.upload_project_modified_files(execution_metadata.project_prfx)
        self.__send_status(execution_metadata, "Ended")

    def __cancel_execution(self, running_process):
        counter = 30
        if running_process.poll() is not None:
            if counter > 0:
                running_process.terminate()
            else:
                running_process.kill()
            time.sleep(1)
        return

    def __check_cancel_request(self, execution_metadata):
        return

    def __send_status(self, execution_metadata, main_status):
        status_message = "{cmdId:\"" + execution_metadata.command_id + "\", status:\""+main_status+"\", vmName:\""+self.connector.myMachineName+"\"}"
        self.connector.send_status(status_message)

    def __shutdown_myself(self):
        self.connector.shutdown_myself()
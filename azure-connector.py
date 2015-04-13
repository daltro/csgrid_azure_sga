# coding=UTF-8

import sys, time, json
from daemon import Daemon
from azure.storage import QueueService
from azure import WindowsAzureError
from azure.storage import BlobService
from sga_shared_data_structures import CommandMetadata
import datetime, os, socket

def create(config):
    return AzureConnector(config)

class AzureConnector():

    def __init__(self, config):
        self.queue_service = QueueService(account_name=config.get("azure", "account_name"),
                                          account_key=config.get("azure", "account_key"))
        self.task_queue_name = config.get("azure", "task_queue_name")
        self.status_queue_name = config.get("azure", "status_queue_name")

        self.private_queue_name = "private_"+config.get("sga", "name")

        self.queue_service.create_queue(self.task_queue_name, fail_on_exist=False)
        # self.queue_service.create_queue(self.private_queue_name, fail_on_exist=False)
        self.queue_service.create_queue(self.status_queue_name, fail_on_exist=False)
        self.algo_storage_name = config.get("azure", "algorithm_storage_name")
 
        self.storage = BlobService(account_name=config.get("azure", "account_name"),
                                   account_key=config.get("azure", "account_key"))

        self.storage.create_container(self.algo_storage_name, fail_on_exist=False)

        self.proj_storage_name = config.get("azure", "project_storage_name")
        self.storage.create_container(self.proj_storage_name, fail_on_exist=False)

    def check_new_tasks(self):

        messages = self.queue_service.get_messages(queue_name=self.task_queue_name,
                                                   numofmessages=1)
        for message in messages:

            self.queue_service.delete_message(self.task_queue_name, message.message_id, message.pop_receipt)

            job_description = json.loads(message.message_text)
            
            command = CommandMetadata(
                command_id = job_description["command_id"],
                algorithm_bin_file = job_description["algorithm_bin_file"],
                project_prfx = job_description["project_prfx"],
                project_input_files = job_description["project_input_files"],
                algorithm_executable_name = job_description["algorithm_executable_name"],
                algorithm_parameters = job_description["algorithm_parameters"],
                sent_timestamp = datetime.datetime.strptime(job_description["sent_timestamp"], "%d/%m/%Y %H:%M:%S"),
                machine_size=job_description["machine_size"])

            # Retornar dados sobre o comando consumido da fila
            return command

        # Não há nada na fila
        return None

    def download_algo_zip(self, algorithm_bin_file, tmp_file):

        for tries in range(1,5):
            try:
                self.storage.get_blob_to_path(self.algo_storage_name, algorithm_bin_file, tmp_file,
                                 open_mode='wb', snapshot=None, x_ms_lease_id=None,
                                 progress_callback=None)
                break

            except:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando...")


    def download_file_to_project(self, project_name, blob_name, dir):

        for tries in range(1,5):
            try:
                self.storage.get_blob_to_path(self.proj_storage_name,
                                              os.path.join(project_name,blob_name),
                                              os.path.join(dir,blob_name),
                                              open_mode='wb', snapshot=None, x_ms_lease_id=None,
                                              progress_callback=None)
                break

            except:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando...")


    def send_status(self, main_status):
        for tries in range(1,5):
            try:
                self.queue_service.put_message(queue_name=self.status_queue_name,
                                               message_text=main_status,
                                               messagettl=10)
                break

            except:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando...")


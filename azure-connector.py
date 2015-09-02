#!/usr/bin/python
#  coding=UTF-8

try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET

import sys, time, json
from daemon import Daemon
from azure.servicebus import ServiceBusService, Message, Queue
from azure.storage.blob import BlobService
from azure.servicemanagement import *
from sga_shared_data_structures import CommandMetadata
import datetime, os, socket

def create(config):
    return AzureConnector(config)

class AzureConnector():

    def __init__(self, config):

        tree = ET.parse('SharedConfig.xml')
        self.myMachineName = tree.find('//Instance').get("id")

        self.sms = ServiceManagementService(
            subscription_id=config.get("azure", "subscription_id"),
            cert_file=config.get("azure", "cert_file")
        );
        self.sms.list_role_sizes()

        self.bus_service = ServiceBusService(
            service_namespace=config.get("azure", "bus_namespace"),
            shared_access_key_name=config.get("azure", "bus_shared_access_key_name"),
            shared_access_key_value=config.get("azure", "bus_shared_access_key_value"))

        self.command_queue = config.get("azure", "commandQueuePath")
        self.bus_service.create_queue(self.command_queue)
        self.status_topic = config.get("azure", "statusTopicPath")
        self.bus_service.create_queue(self.status_topic)

        self.storage = BlobService(account_name=config.get("azure", "account_name"),
                                   account_key=config.get("azure", "account_key"))

        self.algo_storage_name = config.get("azure", "algorithm_storage_name")
        self.storage.create_container(self.algo_storage_name, fail_on_exist=False)

        self.proj_storage_name = config.get("azure", "project_storage_name")
        self.storage.create_container(self.proj_storage_name, fail_on_exist=False)

    def check_new_tasks(self):

        message = self.bus_service.receive_queue_message(self.command_queue, peek_lock=False, timeout=120)

        if message is None or message.body is None:
            return None

        job_description = json.loads(message.body)

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

    def list_algo_files(self, prfx):

        list = self.storage.list_blobs(container_name=self.algo_storage_name, prefix=prfx)
        result = []
        for blob in list:
            result.append(blob.name)
        return result

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

    def download_file_to_algo(self, blob_name, dir):

        for tries in range(1,5):
            try:
                self.storage.get_blob_to_path(container_name=self.algo_storage_name,
                                              blob_name=os.path.join(blob_name),
                                              file_path=os.path.join(dir,blob_name),
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
                self.bus_service.send_topic_message(topic_name=self.status_topic,
                                                    message=main_status)
                break

            except:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando...")

    def shutdown_myself(self):
        # A máquina virtual irá cometer suicídio.
        print("Removendo máquina virtual da nuvem...")
        #self.sms.delete_hosted_service(self.myMachineName)
        exit()
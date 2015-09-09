#!/usr/bin/python
#coding=UTF-8

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
        self.myMachineName = tree.find('.//Instance').get("id")

        self.sms = ServiceManagementService(
            subscription_id=config.get("azure", "subscription_id"),
            cert_file=config.get("azure", "cert_file")
        );

        self.bus_service = ServiceBusService(
            service_namespace=config.get("azure", "bus_namespace"),
            shared_access_key_name=config.get("azure", "bus_shared_access_key_name"),
            shared_access_key_value=config.get("azure", "bus_shared_access_key_value"))

        self.command_queue = config.get("azure", "commandQueuePath")
        for tries in range(1,10):
            try:
                self.bus_service.create_queue(self.command_queue)
                break
            except:
                print "Esperando"
            
        self.status_topic = config.get("azure", "statusTopicPath")
        self.bus_service.create_queue(self.status_topic)

        self.storage = BlobService(account_name=config.get("azure", "account_name"),
                                   account_key=config.get("azure", "account_key"))

        self.algo_storage_name = config.get("azure", "algorithm_storage_name")
        self.storage.create_container(self.algo_storage_name, fail_on_exist=False)

        self.proj_storage_name = config.get("azure", "project_storage_name")
        self.storage.create_container(self.proj_storage_name, fail_on_exist=False)

    def check_new_tasks(self):

        for tries in range(1,2):
            try:
                message = self.bus_service.receive_queue_message(self.command_queue, peek_lock=False, timeout=60)
                break
            except:
                message = None

        if message is None or message.body is None:
            return None

        job_description = json.loads(message.body.replace('/AzureBlobStorage/', ''))

        command = CommandMetadata(
            command_id = job_description["command_id"],
            algorithm_directory = job_description["algorithm_prfx"],
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
        print "download_algo_zip(algorithm_bin_file="+algorithm_bin_file+", tmp_file="+tmp_file+")"
        for tries in range(1,5):
            try:
                self.storage.get_blob_to_path(self.algo_storage_name, algorithm_bin_file, tmp_file,
                                 open_mode='wb', snapshot=None, x_ms_lease_id=None,
                                 progress_callback=None)
                break

            except Exception as e:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando..." + e.__str__())

    def download_file_to_project(self, project_name, blob_name, dir):
        print "download_file_to_project(project_name="+project_name+", blob_name="+blob_name+", dir="+dir+")"
        for tries in range(1,5):
            try:
                self.storage.get_blob_to_path(self.proj_storage_name,
                                              os.path.join(project_name,blob_name),
                                              os.path.join(dir,os.path.join(project_name,blob_name)),
                                              open_mode='wb', snapshot=None, x_ms_lease_id=None,
                                              progress_callback=None)
                break

            except Exception as e:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando..." + e.__str__())

    def download_file_to_project(self, project_name, blob_name, dir):
        print "download_file_to_project(project_name="+project_name+", blob_name="+blob_name+", dir="+dir+")"
        for tries in range(1,5):
            try:
                self.storage.get_blob_to_path(self.proj_storage_name,
                                              os.path.join(project_name,blob_name),
                                              os.path.join(dir,os.path.join(project_name,blob_name)),
                                              open_mode='wb', snapshot=None, x_ms_lease_id=None,
                                              progress_callback=None)
                break

            except Exception as e:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando..." + e.__str__())

    def upload_proj_file(self, project_name, blob_name, dir):
        print "upload_proj_file(project_name="+project_name+", blob_name="+blob_name+", dir="+dir+")"
        if blob_name[0] == '/':
            blob_name = blob_name[1:]
        for tries in range(1,5):
            try:
                self.storage.put_block_blob_from_path(self.proj_storage_name,
                                              os.path.join(project_name,blob_name),
                                              os.path.join(dir,os.path.join(project_name,blob_name)))
                break

            except Exception as e:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando..." + e.__str__())

    def download_file_to_algo(self, blob_name, dir):
        print "download_file_to_algo(blob_name="+blob_name+", dir="+dir+")"

        for tries in range(1,5):
            try:
                self.storage.get_blob_to_path(container_name=self.algo_storage_name,
                                              blob_name=os.path.join(blob_name),
                                              file_path=os.path.join(dir,blob_name),
                                              open_mode='wb', snapshot=None, x_ms_lease_id=None,
                                              progress_callback=None)
                break

            except Exception as e:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando..." + e.__str__())


    def send_status(self, main_status):
        for tries in range(1,5):
            try:
                self.bus_service.send_topic_message(topic_name=self.status_topic,
                                                    message=Message(main_status.encode('utf-8')))
                break

            except Exception as e:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando..." + e.__str__())

    def shutdown_myself(self):

        return

        # A máquina virtual irá cometer suicídio.
        print("Removendo máquina virtual da nuvem...")
        for tries in range(1,5):
            try:
                self.sms.delete_deployment(
                    service_name=self.myMachineName,
                    deployment_name=self.myMachineName, delete_vhd=True)
                exit(0)
                break

            except Exception as e:

                if tries == 5:
                    print("Muitos erros de conexão. Operação abortada.")
                else:
                    print("Erro de conexão com serviço. Retentando..." + e.__str__())

        #self.sms.delete_hosted_service(self.myMachineName)
        #self.sms.shutdown_role(service_name=self.myMachineName,
        #                       deployment_name=self.myMachineName,
        #                       role_name=self.myMachineName,
        #                       post_shutdown_action="StoppedDeallocated")

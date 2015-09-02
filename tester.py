from azure import WindowsAzureError

__author__ = 'daltrogama'

from azure.storage import QueueService
import json, datetime

queue_service = QueueService(account_name='csgridprojects',
                             account_key='9Qnn05reSrOCoDNOtz6aHCuLz5/Bmad+3Am5qSG208QCZBKoqDQxPFHSXsWxuvgfwpB6DEKrdNXD8Ud7cB1k4w==')
try:
    print "Inicializando filas..."
    queue_service.create_queue('taskqueue', fail_on_exist=False)
    queue_service.create_queue('statusqueue', fail_on_exist=False)


    json_message = """{
    "command_id": "abcd-1234",
    "algorithm_prfx": "run.zip",
    "project_prfx": "happyProject",
    "project_input_files": ["build.xml", "names.csv"],
    "algorithm_executable_name": "run.sh",
    "algorithm_parameters": [],
    "sent_timestamp": "12/01/2015 10:00:00",
    "machine_size": "*"
    }"""

    #
    # job_description = json.loads(json_message)
    #
    # command_id = job_description["command_id"],
    # algorithm_bin_file = job_description["algorithm_bin_file"],
    # project_prfx = job_description["project_prfx"],
    # project_input_files = job_description["project_input_files"],
    # algorithm_executable_name = job_description["algorithm_executable_name"],
    # algorithm_parameters = job_description["algorithm_parameters"],
    # sent_timestamp = datetime.datetime.strptime(job_description["sent_timestamp"], "%d/%m/%Y %H:%M:%S")

    print "Enviando mensagem..."
    queue_service.put_message('taskqueue', json_message)
    print "Mensagem enviada. Checando agora a fila de status."

    try:
        while True:
            print ">"
            status_messages = queue_service.get_messages('statusqueue')
            for message in status_messages:
                queue_service.delete_message('statusqueue', message.message_id, message.pop_receipt)
                print message.message_text

    except KeyboardInterrupt:
        print "tchau."

except WindowsAzureError, e:
    print e.message
__author__ = 'daltrogama'

from azure.storage import QueueService
import json, datetime

queue_service = QueueService(account_name='csgridprojects',
                             account_key='R4S6zMp/Yy0FMG+FW/q5B1NCpTVbjsSX9YN3t8kozyR1ylhOgv9DcliTDoDDU8v6LuBgr/GT5lI9sSMaYzeJ6Q==')

print "Inicializando filas..."
queue_service.create_queue('taskqueue')
queue_service.create_queue('statusqueue')


json_message = """{
"command_id": "abcd-1234",
"algorithm_bin_file": "storage_algo_file.zip",
"project_prfx": "storage_prefix",
"project_input_files": ["file1", "file2"],
"algorithm_executable_name": "exec.sh",
"algorithm_parameters": [],
"sent_timestamp": "12/01/2015 10:00:00"
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
__author__ = 'daltrogama'

import json, datetime
from azure.servicebus import ServiceBusService, Message, Queue


bus_service = ServiceBusService(
            service_namespace='csgriddaltro',
            shared_access_key_name='RootManageSharedAccessKey',
            shared_access_key_value='t2lyxPaILuLgGxmzyKIBPWpYgPDL1cotvoLNw0qxBL4=')

json_message = """{
"command_id": "admi@test.CBJ6LTHDWM",
"algorithm_prfx": "algorithms/TATU/versions/v_001_000_000/bin/Linux26g4_64",
"project_prfx": "/AzureBlobStorage/sandbox/admin/tester/admi_test_CBJ6LTHDWM",
"project_input_files": [".cmds/admi_test_CBJ6LTHDWM/cmd.parameters", "tatu-a-b-lab-times.pdf", ".cmds/admi_test_CBJ6LTHDWM/script.ksh", ".cmds/admi_test_CBJ6LTHDWM/cmd.properties"],
"algorithm_executable_name": "/bin/ksh",
"algorithm_parameters": ["/AzureBlobStorage/sandbox/admin/tester/admi_test_CBJ6LTHDWM/.cmds/admi_test_CBJ6LTHDWM/script.ksh"],
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
bus_service.send_queue_message('commands', Message(json_message))
print "Mensagem enviada. Checando agora a fila de status."

try:
    bus_service.create_subscription('status', 'tester_sub')
    while True:
        print ">"
        status_message = bus_service.receive_subscription_message('status', 'tester_sub', peek_lock=False)
        print status_message.body

except KeyboardInterrupt:
    print "tchau."

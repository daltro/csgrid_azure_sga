#!/usr/bin/python
#  coding=UTF-8

import sys
from sga_main_thread import SgaDaemon

if __name__ == "__main__":
    daemon = SgaDaemon('/tmp/sga-daemon.pid')
    if len(sys.argv) == 2:
        if 'start' == sys.argv[1]:
            daemon.start()
        elif 'test' == sys.argv[1]:
            daemon.run()
        elif 'stop' == sys.argv[1]:
            daemon.stop()
        elif 'restart' == sys.argv[1]:
            daemon.restart()
        else:
            print "Unknown command"
            sys.exit(2)
        sys.exit(0)
    else:
        print "usage: %s start|stop|restart" % sys.argv[0]
        sys.exit(2)
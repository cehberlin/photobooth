#!/usr/bin/env python
# Requires Python for Windows Extensions: http://python.net/crew/skippy/win32/
# IrfanView applies the last successfully executed print configurations if it is
# called from the commandline, hence you have to print once with your intended 
# settings. Moreover, you have to adjust the service configuration to use your
# current user account for execution in order to apply these configs for the 
# service. Alternatively you can create a special account for this service.

import subprocess
import os
import glob
import time
import win32serviceutil
import win32service
import win32event
import servicemanager
import traceback

# directory that is monitored for photos to print, printed photos are deleted (just provice a copy)
MONITORED_FOLDER = "D:/test"
MONITORED_FOLDER_INFO_FILE = MONITORED_FOLDER + '/FILES IN THIS DIRECTORY with .jpg EXTENSION are automatically printed and DELETED'
IRFAN_VIEW = "C:\Program Files (x86)\IrfanView\i_view32.exe"  # or add i_view32.exe to path
PRINTER_NAME = "Canon Inkjet SELPHY DS810"
MONITORING_TIMEOUT_PERIOD = 10  # seconds


class AppServerSvc(win32serviceutil.ServiceFramework):
    _svc_name_ = "PythonPrintMonitor"
    _svc_display_name_ = "Python Print Monitor"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)

    def SvcStop(self):
        self._running = False
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STOPPED,
                              (self._svc_name_, ''))
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.hWaitStop)

    def SvcDoRun(self):
        servicemanager.LogMsg(servicemanager.EVENTLOG_INFORMATION_TYPE,
                              servicemanager.PYS_SERVICE_STARTED,
                              (self._svc_name_, ''))

        # check if folder exists
        if not os.path.exists(MONITORED_FOLDER):
            os.makedirs(MONITORED_FOLDER)
            servicemanager.LogInfoMsg("Monitored folder doesn't exist. Creating: '" + MONITORED_FOLDER + "'")
        #create info file in directory
        if not os.path.exists(MONITORED_FOLDER_INFO_FILE):
            f = open(MONITORED_FOLDER_INFO_FILE, "a")
            f.close()

        self._running = True
        self.main()

    def print_photo(self, file):
        #this complicated string formatting was necessary to deal with spaces in arguments and process names
        p = subprocess.Popen("{0} {1} /print={2}".format(IRFAN_VIEW, r'"%s"' % file, r'"%s"' % PRINTER_NAME))
        p.wait()

    def main(self):
        while self._running:
            try:
                files = glob.glob(MONITORED_FOLDER + "/*.jpg")

                # Enable for debugging
                #if len(files)==0:
                #    servicemanager.LogInfoMsg("No photos found.")
                for file in files:
                    # convert to windows \ convention
                    photo_file = file.replace("/", "\\")
                    servicemanager.LogInfoMsg("Printing photo: '" + photo_file+"'")
                    self.print_photo(photo_file)
                    os.remove(file)
            except Exception as e:
                servicemanager.LogMsg(servicemanager.EVENTLOG_ERROR_TYPE,
                                      servicemanager.PYS_SERVICE_STARTED,
                                      (self._svc_name_, ' ' + str(e) + '\n' + traceback.format_exc()))
            time.sleep(MONITORING_TIMEOUT_PERIOD)


if __name__ == '__main__':
    win32serviceutil.HandleCommandLine(AppServerSvc)


from smb.SMBConnection import SMBConnection
import os
import subprocess
from wakeonlan import wol
import shlex

SMB_USER = 'pi'
SMB_PW = 'Test1234'
SERVER_NAME = 'pi-printer'
SMB_SHARE = 'photos'
SERVER_IP = '192.168.10.2'
SERVER_MAC = '00.e0.4b.3e.f0.74'
CLIENT_NAME = 'raspberry'


def start_printer():
    wol.send_magic_packet(SERVER_MAC, ip_address=SERVER_IP)

def stop_printer():
    "net rpc shutdown -I 192.168.10.2 -U pi%Test1234 -f"

    command = "net rpc shutdown -I {0} -U {1}%{2} -f".format(SERVER_IP, SMB_USER, SMB_PW )
    args = shlex.split(command)
    subprocess.check_call(args)

def printer_available():

    try:
        conn = SMBConnection(SMB_USER, SMB_PW,
                             CLIENT_NAME, SERVER_NAME,
                             use_ntlm_v2=False)
        if conn.connect(SERVER_IP, 139, timeout = 2):
            conn.close()
            return True
        else:
            return False
    except:
        return False

    return True

def print_photo(photo_file):
    """
    printing a photo on a remote printer
    In this case we copy the file with smb to a remote windows server that monitors that share and prints the files
    """

    conn = SMBConnection(SMB_USER, SMB_PW,
                         CLIENT_NAME, SERVER_NAME,
                         use_ntlm_v2=False)
    dest_file_name = os.path.basename(photo_file)
    tmp_file_name = dest_file_name + '.tmp'
    if conn.connect(SERVER_IP, 139):
        with open(photo_file, 'r') as fp:
            fp.seek(0)
            #first store in a temporary file to avoid that the print daemon starts with an incomplete file
            conn.storeFile(SMB_SHARE, tmp_file_name, fp)
            #rename to final file name
            conn.rename(SMB_SHARE, tmp_file_name, dest_file_name)
        conn.close()
    else:
        print('Cannot connect to server')


if __name__ == '__main__':
    test_foto ='preview.jpg'
    #print_photo(test_foto)
    start_printer()

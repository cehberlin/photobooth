
from smb.SMBConnection import SMBConnection
import os

SMB_USER = 'pi'
SMB_PW = 'Test1234'
SERVER_NAME = 'toffer'
SMB_SHARE = 'test'
SERVER_IP = '192.168.0.32'
CLIENT_NAME = 'raspberry'

def print_photo( photo_file):
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
    test_foto ='snap2.jpg'
    print_photo(test_foto)
import json
import requests

import datetime
import filecmp
from paramiko import SSHClient
from scp import SCPClient

url_getAuthToken = 'http://localhost:8000/api-auth-token/'
url_getFilenameHashes = 'http://localhost:8000/fft-api/getFilenameHashes/api_testing/test_1/'
baseurl_reportFileTransfer = 'http://localhost:8000/fft-api/reportFileTransfer/'
baseurl_fileMetadata = 'http://localhost:8000/fft-api/fileMetadata/'

auth_request = { "username": "client", "password": "ftTestPW" }

print( "\nGET AUTHENTICATION TOKEN" )
print( "request url: {}".format(url_getAuthToken) )
print( "request data:\n", json.dumps( auth_request, indent=2 ) )
auth_response = requests.post( url_getAuthToken, json=auth_request )
print( "response:")
print( "status {}".format(auth_response.status_code) )
auth_response_data = auth_response.json()
print ( "{}\n".format( json.dumps(auth_response_data, indent=2) ) )

token = auth_response_data["token"]

head = { "Authorization": "token {}".format(token) }

files_to_transfer = [
            { "name_orig": "measurement1.txt" },
            { "name_orig": "measurement1.png" },
            { "name_orig": "measurement2.txt" },
            { "name_orig": "measurement2.png" },
        ]
md = [
        { "field": "meta1", "value": "data1" },
        { "field": "meta2", "value": "data2" },
        { "field": "meta3", "value": "data3" }
    ]
print( "\nREQUEST HASHED FILENAMES TO USE ON STORAGE SYSTEM")
print( "request url:\n  {}".format(url_getFilenameHashes) )
print( "request data:\n", json.dumps( files_to_transfer, indent=2 ) )
response = requests.post(url_getFilenameHashes, json=files_to_transfer, headers=head)
print( "response:")
print( "  status {}".format(response.status_code) )
response_data = response.json()
print ( "{}\n".format( json.dumps(response_data, indent=2) ) )

if (response.status_code == 200):
    file_hash_pair = response_data[0]
    local_file = file_hash_pair['name_orig']
    remote_file = '/tmp/{}'.format(file_hash_pair['name_hash'])

    now = datetime.datetime.now()
    f = open(local_file, 'w')
    f.write("Current data and time:\n")
    f.write("{}\n".format(now.strftime("%Y-%m-%d %H:%M:%S")))
    f.close()

    print( "\nCOPY FILE" )
    print( "scp {} transferuser@storage_computer:{}".format(local_file, remote_file) )

    ssh = SSHClient()
    ssh.load_system_host_keys()
    ssh.connect('localhost')
    scp = SCPClient(ssh.get_transport())
    scp.put( file_hash_pair['name_orig'], remote_path=remote_file )
    scp.close()

    if filecmp.cmp( file_hash_pair['name_orig'], remote_file ):
        print( "  successful copy\n\n" )

        print( "REPORT FILE TRANSFER SUCCESS" )
        url_reportFileTransfer = "{}{}/".format(baseurl_reportFileTransfer, file_hash_pair["name_hash"])
        print( "request url:\n  {}".format(url_reportFileTransfer) )
        response = requests.put(url_reportFileTransfer, json={"name_orig": file_hash_pair["name_orig"]}, headers=head)
        print( "response:" )
        print( "  status {}".format( response.status_code ) )

        print( "\nADD METADATA" )
        url_fileMetadata = '{}{}/'.format(baseurl_fileMetadata, file_hash_pair['name_hash'])
        print( "request url:\n  {}".format(url_fileMetadata) )
        for x in md:
            print( "request data:\n", json.dumps(x, indent=2) )
            response = requests.post(url_fileMetadata, json=x, headers=head)
            print( "response:\n  status {}".format(response.status_code) )

        print( "\nRETRIEVE METADATA" )
        print( "request url:\n  {}".format(url_fileMetadata) )
        response = requests.get(url_fileMetadata, headers=head)
        response_data = response.json()
        print( "response:\n  status {}\n".format(response.status_code), json.dumps(response_data, indent=2) )
    else:
        print( "  !!!COPY FAILED!!!\n" )

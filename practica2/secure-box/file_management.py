"""
file_management
Contains the main functionality for managing the files
Most functions have complete functionality and don't
return any value, printing the process output
Authors:
    Ana Calzada
    Martin Sanchez
"""

import re
import os
import sys
import requests
import encryption
from Cryptodome.PublicKey import RSA

token = 'IMPORT TOKEN HERE'

def upload(file, dest_id):
    """ Upload a file.
    Given the file (path) and the id of the destinatary, it
    encrypts and signs the file and then uploads it.
    """
    # Get file and private key
    data, filename = read_from_file(file)
    if data is None:
        return

    key_pr = encryption.get_key()
    if key_pr is None:
        print('\nError: No private key found, create an id first with --create_id', file=sys.stderr)
        return

    # Sign file
    print('Solicitando envío de fichero a SecureBox')
    print('-> Firmando fichero...', end='', flush=True)
    try:
        signature, data = encryption.sign_data(data, key_pr)
    except:
        print('\nError: Could not sign file, error with private key', file=sys.stderr)
        return
    print('OK', flush=True)

    # Retrieve public key from dest
    print('-> Recuperando clave pública de ID {0}...'.format(dest_id), end='', flush=True)
    r = encryption.request_public_key(dest_id)
    if r.status_code != 200:
        print_error_server(r)
        return
    key_pu = RSA.import_key(r.json()['publicKey'])
    print('OK', flush=True)

    # Encrypt with public key
    print('-> Cifrando fichero...', end='', flush=True)
    try:
        iv, enc_session_key, enc_data = encryption.encrypt_data(signature+data, key_pu)
    except:
        print('\nError: Could not encrypt file, error with public key', file=sys.stderr)
        return
    to_send = iv + enc_session_key + enc_data
    print('OK', flush=True)

    # Upload
    print('-> Subiendo fichero al servidor...', end='', flush=True)
    url = 'https://vega.ii.uam.es:8080/api/files/upload'
    file = {'ufile': (filename, to_send)}
    headers = {'Authorization': 'Bearer '+token}
    r = requests.post(url, files=file, headers=headers)

    if r.status_code != 200:
        print_error_server(r)
        return
    print('OK', flush=True)
    print('Subida realizada correctamente, ID del fichero: {0}'.format(r.json()['file_id']))
    return


def download_file(file_id, src_id):
    """ Downloads a file.
    Given a file id (created on upload), it fetches it from
    the server and then tries to decrypt it.
    """
    # Get private key to decrypt
    key_pr = encryption.get_key()
    if key_pr is None:
        print('\nError: No private key found, create an id first with --create_id', file=sys.stderr)
        return

    # Fetch file
    print('Descargando fichero de SecureBox...', end='',flush=True)
    url = 'https://vega.ii.uam.es:8080/api/files/download'
    args = {'file_id': file_id}
    headers = {'Authorization': 'Bearer '+token}
    r = requests.post(url, json=args, headers=headers)

    if r.status_code != 200:
        print_error_server(r)
        return
    content = r.content

    # Retrieve original filename with regex
    try:
        regex = r"(?<=filename=\")(?:[^\"\\]|\\.)*(?=\")"
        matches = re.findall(regex, r.headers['Content-Disposition'])
        if len(matches) > 0:
            filename = matches[0]
        else:
            filename = 'download'
    except:
        filename = 'download'

    print('OK',flush=True)
    print('-> {0} bytes descargados correctamente'.format(len(content)),flush=True)

    # Decrypt content and verify
    print('-> Descifrando fichero...',end='',flush=True)
    try:
        iv, enc_session_key, enc_data = encryption.get_encrypted_components(content)
        data = encryption.decrypt_data(iv, enc_session_key, enc_data, key_pr)
    except:
        print('\nError: Could not decrypt file, invalid private key', file=sys.stderr)
        return
    print('OK', flush=True)

    # Get public key to verify
    print('-> Recuperando clave pública de ID {0}...',end='',flush=True)
    r = encryption.request_public_key(src_id)
    if r.status_code != 200:
        print_error_server(r)
        return
    key_pu = RSA.import_key(r.json()['publicKey'])
    print('OK',flush=True)

    print('-> Verificando firma...',end='',flush=True)
    signature, data = encryption.get_signed_components(data)
    if encryption.verify_data(signature, data, key_pu):
        print('OK',flush=True)
    else:
        print('\nError: Sign verification failed', file=sys.stderr)

    if write_in_file(filename, data):
        print('Fichero \'{0}\' descargado y verificado correctamente'.format(filename))
    return


def list_files():
    """ Prints a list of files.
    Accesses the server to retrieve the list of files under the
    current user.
    """
    # Make request
    url = 'https://vega.ii.uam.es:8080/api/files/list'
    headers = {'Authorization': 'Bearer '+token}

    print('Recuperando lista de ficheros subidos al servidor...',end='',flush=True)
    r = requests.post(url, headers=headers)

    if r.status_code != 200:
        print_error_server(r)
        return
    print('OK',flush=True)

    # Print results
    json = r.json()
    num = json['num_files']
    files = json['files_list']
    print('Se han encontrado {0} ficheros:'.format(num))
    for i in range(num):
        print('[{index}] {name}, ID: {id}'.format(index=i, name=files[i]['fileName'], id=files[i]['fileID']))

    return


def delete_file(id):
    """ Deletes a files.
    Given a valid file id (of a file owned by the user), it
    tries to delete it from the server.
    """
    url = 'https://vega.ii.uam.es:8080/api/files/delete'
    args = {'file_id': id}
    headers = {'Authorization': 'Bearer '+token}

    print('Solicitando borrado del fichero #{0}...'.format(id),end='',flush=True)
    r = requests.post(url, json=args, headers=headers)

    if r.status_code != 200:
        print_error_server(r)
        return
    print('OK',flush=True)
    print('Fichero con fileID#{0} borrado correctamente'.format(id))

    return


def get_abs_path(rel_path):
    script_dir  = os.path.dirname(__file__)
    abs_path    = os.path.join(script_dir, rel_path)
    return abs_path


def write_in_file(file, data):
    """ Write data in file and print in case of error.
    Returns True if success,
            False if error
    """
    # Save file
    try:
        f = open(file, 'wb')
        f.write(data)
        f.close()
    except:
        print('\nError: Could not save output in {0}'.format(file), file=sys.stderr)
        return False
    return True

def read_from_file(file):
    """ Read data and name from file and print in case of error.
    Returns data and filename if success,
            None if error
    """
    try:
        f = open(file, 'rb')
        data = f.read()
        name = os.path.basename(file)
        f.close()
    except:
        print('\nError: Could not find file {0}'.format(file), file=sys.stderr)
        return None
    return data, name


def print_error_server(response):
    """ Print error message from server response
    """

    if response.status_code > 499:
        print('\nError: Server fault responded with code {0}'.format(response.status_code), file=sys.stderr)
        return

    if response.status_code == 401 or response.status_code == 403:
        print('\nError: Server responded with code {0}'.format(response.status_code), end='', file=sys.stderr)
        try:
            print(': {0}'.format(response.json()['description']),file=sys.stderr)
        except:
            print(': No description',file=sys.stderr)
        return

    print('\nError: Causa desconocida', file=sys.stderr)
    return

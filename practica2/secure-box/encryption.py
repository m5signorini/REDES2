"""
encryption
Contains the functionality to encrypt files and sign them
Authors:
    Ana Calzada
    Martin Sanchez
"""

import os
import sys
import requests
import argparse
from file_management import write_in_file, read_from_file, print_error_server

from Cryptodome.PublicKey import RSA
from Cryptodome.Hash import SHA256
from Cryptodome.Cipher import AES, PKCS1_OAEP
from Cryptodome.Signature import pkcs1_15
from Cryptodome.Random import get_random_bytes
from Cryptodome.Util.Padding import pad, unpad

token = 'IMPORT TOKEN HERE'
user_data_dir = None
private_key_path = None


def generate_encrypted_signed_file(file, key_pr=None, key_pu=None, id=None, output=None):
    """ Generate signed and then encrypted file.
    Given a file, it gets signed and then encrypted.
    """
    default_args = get_default_args(file, key_pr=key_pr, key_pu=key_pu, id=id, out_se=output)
    if default_args is None:
        return
    if key_pr is None:
        key = default_args['key_pr']
    if key_pu is None:
        key = default_args['key_pu']
    if output is None:
        output = default_args['out_se']

    # Read data
    data, name = read_from_file(file)
    if data is None:
        return

    # Sign data
    try:
        signature, data = sign_data(data, key_pr)
    except:
        print('Error: Could not sign, invalid data or key', file=sys.stderr)
        return

    # Encrypt signed data
    try:
        iv, enc_session_key, enc_data = encrypt_data(signature + data, key_pu)
    except:
        print('Error: Could not encrypt, invalid data or key', file=sys.stderr)
        return

    # Write data
    if write_in_file(output, iv + enc_session_key + enc_data) is False:
        return
    print('Archivo {0} ha sido encriptado y firmado correctamente y guardado como {1}'.format(file, output))
    return

def generate_encrypted_file(file, key=None, id=None, output=None):
    """ Encrypts a local file.
    Given a file (path) and the destinatary id, it encrypts
    the file locally so that only the one with the dest_id is
    able to decrypt it.
    Default public key is obtained from the server, can use other key.
    If no public key and no id are given, prints an error.
    """
    # Get default arguments and return in case of error
    default_args = get_default_args(file, key_pu=key, id=id, out_e=output)
    if default_args is None:
        return
    if key is None:
        key = default_args['key_pu']
    if output is None:
        output = default_args['out_e']

    # Read file
    data, name = read_from_file(file)
    if data is None:
        return

    # Encrypt data
    try:
        iv, enc_session_key, enc_data = encrypt_data(data, key)
    except:
        print('Error: Could not encrypt, invalid data or key', file=sys.stderr)
        return

    # Write file
    if write_in_file(output, iv + enc_session_key + enc_data) is False:
        return

    print('Archivo {0} ha sido encriptado correctamente y guardado como {1}'.format(file, output))
    return


def generate_signed_file(file, key=None, output=None):
    """ Generate signed file.
    Signs a file and saves it as output.
    Default output appends _signed to the filename.
    Default key is the one stored at user-data
    """
    # Get default arguments and return in case of error
    default_args = get_default_args(file, key_pr=key, out_s=output)
    if default_args is None:
        return
    if key is None:
        key = default_args['key_pr']
    if output is None:
        output = default_args['out_s']

    # Read file
    data, name = read_from_file(file)
    if data is None:
        return

    # Sign data
    try:
        signature, data = sign_data(data, key)
    except:
        print('Error: Could not sign, invalid data or key', file=sys.stderr)
        return

    # Write file
    if write_in_file(output, signature + data) is False:
        return

    print('Archivo {0} ha sido firmado correctamente y guardado como {1}'.format(file, output))
    return


def verify_file(file, key):
    """ Verify signed file.
    Expected a file starting with the SHA256 signature
    encrypted with RSA using bits and then the unaltered data.
    Expected the public key also.
    """
    # Read signature and data
    try:
        f = open(file, 'rb')
        signature = f.read(key.size_in_bytes())
        data = f.read()
        f.close()
    except:
        print('Error: Could not read file {0}'.format(file), file=sys.stderr)
        return False

    # Verify
    if verify_data(signature, data, key) is True:
        print('Archivo {0} verificado correctamente'.format(file))
    else:
        print('Archivo {0} corrupto'.format(file))
        return False
    return True


def verify_encrypted_file(file, key_pr, key_pu):
    """ Verify encrypted and signed file.
    Verifies a file that has been encryped with AES and RSA,
    and signed with SHA256.
    AES uses IV of 16 bytes and session_key of 32 bytes
    """
    try:
        f = open(file, 'rb')
        data = f.read()
        iv, enc_session_key, enc_data = get_encrypted_components(data)
        f.close()
    except:
        print('Error: Invalid read from file {0}'.format(file), file=sys.stderr)
        return False
    # Decrypt
    try:
        data = decrypt_data(iv, enc_session_key, enc_data, key_pr)
    except:
        print('Error: Could not decrypt, invalid data or key', file=sys.stderr)
        return

    # Verify
    signature, data = get_signed_components(data)

    # Verify
    if verify_data(signature, data, key_pu) is True:
        print('Archivo {0} verificado correctamente'.format(file))
    else:
        print('Archivo {0} corrupto'.format(file))
        return False
    return True


def decrypt_data(iv, enc_session_key, enc_data, key):
    """ Decrypts data using AES and RSA.
    AES: 16 bytes iv, 32 bytes key
    RSA: using private key 'key'
    session key with RSA, data with AES.
    Raises exception if invalid data or key.
    """
    # Retrieve session_key
    cipher_rsa = PKCS1_OAEP.new(key)
    session_key = cipher_rsa.decrypt(enc_session_key)

    # Retrieve data
    cipher_aes = AES.new(session_key, AES.MODE_CBC, iv=iv)
    data = unpad(cipher_aes.decrypt(enc_data), AES.block_size)

    return data


def encrypt_data(data, key):
    """ Encrypts data using AES and RSA.
    AES: 16 bytes iv, 32 bytes key
    RSA: using public key 'key'
    session key with RSA, data with AES.
    Raises exception if invalid data or key.
    """
    # Encrypt data using AES wiht 256 bits (32 bytes) key
    session_key = get_random_bytes(32)
    cipher_aes = AES.new(session_key, AES.MODE_CBC)
    enc_data = cipher_aes.encrypt(pad(data, AES.block_size))
    iv = cipher_aes.iv

    # Encrypt AES key using RSA
    cipher_rsa = PKCS1_OAEP.new(key)
    enc_session_key = cipher_rsa.encrypt(session_key)

    # Output is in format: IV | SYMMETRIC KEY | Data
    return (iv, enc_session_key, enc_data)


def sign_data(data, key):
    """ Signs a local file.
    Given a byte string it signs it using the user private
    RSA key by default.
    Returns byte string with the signature and file.
    Raises exception if invalid data or key.
    """
    # Hash the file with SHA256 and sign it
    hash = SHA256.new(data)
    signature = pkcs1_15.new(key).sign(hash)

    # Output is in format: SIGNATURE | DATA
    return (signature, data)


def verify_data(signature, data, key):
    """ Verify data.
    Given a signature and data, both byte string, verifies the hash
    Returns True if the signature matches the data,
            False if not
    """
    # Verify signature
    try:
        hash = SHA256.new(data)
        pkcs1_15.new(key).verify(hash, signature)
    except:
        return False
    return True

def verify_encrypted_data(data, key_pr, key_pu):
    """ Verify encrypted and signed data.
    """
    return

def get_encrypted_components(data):
    """ Retrieve iv, enc_session_key, enc_data.
    Given encrypted data, it returns the mentioned parts.
    IV of 16 bytes
    Session key encoded with RSA 2048: 256 Bytes
    """
    iv = data[:16]
    enc_session_key = data[16:272]
    enc_data = data[272:]
    return iv, enc_session_key, enc_data

def get_signed_components(data):
    """ Retrieve signature and data
    Given signed data, it returns the mentioned parts.
    """
    signature = data[:256]
    data = data[256:]
    return signature, data

def generate_rsa_key():
    """ Generate RSA key
    Given a length, it generates the public and private parts
    of an RSA key and returns them.
    Returns (private_key, public_key)
    """
    key_pr = RSA.generate(2048)
    key_pu = key_pr.public_key()
    return (key_pr, key_pu)


def get_pem_format(key):
    """ Get PEM format of a key
    Given a key, returns it as a byte string in PEM format
    """
    pem = key.export_key('PEM')
    return pem


def store_key(key, rel_path=None):
    """ Store a key locally.
    Given a key, it gets stored in PEM format in the
    app-specific folder for further retrieval.
    Raises exception in case of error.

    Note that the key is directly stored (exposed) in order
    to avoid the need for user interaction (via passcode).
    For increased security one may opt to generate a random
    pass phrase and have the user input it every time the
    key is needed (not friendly).
    """
    # Obtain PEM format to be stores
    pem = get_pem_format(key)

    # Obtain path for storing (relative to this script)
    if rel_path is None:
        rel_path    = private_key_path

    script_dir  = os.path.dirname(__file__)
    abs_path    = os.path.join(script_dir, rel_path)
    # Write to file
    f = open(abs_path, 'wb')
    f.write(pem)
    f.close()
    return


def get_key(path=None):
    """ Retrieve local key.
    Default option for None is private_key_path.
    Returns the key stored locally at path,
            None if not found
    """
    if path is None:
        path = private_key_path
    try:
        # Obtain path
        script_dir  = os.path.dirname(__file__)
        rel_path    = path
        abs_path    = os.path.join(script_dir, rel_path)

        # Obtain key in PEM format
        f = open(abs_path, 'rb')
        pem = f.read()
        f.close()
    except:
        return None

    return RSA.import_key(pem)

def request_public_key(id):
    """ Retrieve public key from server.
    """
    url  = 'https://vega.ii.uam.es:8080/api/users/getPublicKey'
    args = {'userID': id}
    headers = {'Authorization': 'Bearer '+token}
    return requests.post(url, headers=headers, json=args)

def get_signed_name(file):
    """ Append signed extension.
    Returns new file path,
            None in case of error
    """
    try:
        output='{0}_signed{1}'.format(os.path.splitext(file)[0], os.path.splitext(file)[1])
    except:
        return None
    return output


def get_encrypted_name(file):
    """ Append encrypted extension.
    Returns new file path,
            None in case of error
    """
    try:
        output='{0}_encrypted{1}'.format(os.path.splitext(file)[0], os.path.splitext(file)[1])
    except:
        return None
    return output


def get_default_args(file, key_pr=True, key_pu=True, id=None, out_s=True, out_e=True, out_se=True):
    """ Get default arguments.
    Fills a dictionary with the default value of the arguments
    passed as None or False. Also prints the corresponding results.
    For example, if key_pr is None, the returned dictionary will have
    an attribute called 'key_pr' with the default private key.
    Returns dictionary with the default parameters, or
            None in case of error
    """
    # GET DEFAULT ENCRYPTED OUTPUT
    ###########################
    if not out_e:
        out_e = get_encrypted_name(file)
        if out_e is None:
            print('Error: Invalid file name {0}'.format(file))
            return None

    # GET DEFAULT SIGNED OUTPUT
    ###########################
    if not out_s:
        out_s = get_signed_name(file)
        if out_s is None:
            print('Error: Invalid file name {0}'.format(file))
            return None

    # GET DEFAULT SIGNED AND ENCRYPTED OUTPUT
    #########################################
    if not out_se:
        out_se = get_signed_name(file)
        if out_se is None:
            print('Error: Invalid file name {0}'.format(file))
            return None
        out_se = get_encrypted_name(file)
        if out_se is None:
            print('Error: Invalid file name {0}'.format(file))
            return None

    # GET DEFAULT PUBLIC KEY
    ########################
    if not key_pu:
        if id is None:
            print('Error: No key nor dest_id provided', file=sys.stderr)
            return None
        # Get key from server
        print('Solicitando clave pública de la identidad #{0}...'.format(id), end='', flush=True)
        r = request_public_key(id)
        
        if r.status_code != 200:
            print_error_server(r)
            return None

        print('OK')
        pem = r.json()['publicKey']
        key_pu = RSA.import_key(pem)

    # GET DEFAULT PRIVATE KEY
    #########################
    if not key_pr:
        key_pr = get_key()
        if key_pr is None:
            print('Error: Could not find private RSA key at {0} or none given'.format(private_key_path), file=sys.stderr)
            return None

    return {'key_pr':key_pr, 'key_pu':key_pu, 'out_e':out_e, 'out_s':out_s}

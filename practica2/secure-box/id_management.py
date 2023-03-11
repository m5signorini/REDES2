"""
id_management
Contains the main functionality for managing the user id
Most functions have complete functionality and don't
return any value, printing the process output
Authors:
    Ana Calzada
    Martin Sanchez
"""
import sys
import requests
import encryption
from file_management import print_error_server

token = 'IMPORT TOKEN HERE'

def create_id(name, email, alias):
    """ Create new identity.
    Generates all the necessary information for a new id and
    posts it to the API, overwriting a possible previous saved
    id for the current user.
    """
    # Create public/private key parts with rsa
    print('Generando par de claves RSA...', end='', flush=True)
    key_pr, key_pu = encryption.generate_rsa_key()
    pem_pu = encryption.get_pem_format(key_pu)
    print('OK')

    # Save private key
    try:
        encryption.store_key(key_pr)
    except:
        print('Error: Could not store the key locally', file=sys.stderr)
        return

    # Call API
    url  = 'https://vega.ii.uam.es:8080/api/users/register'
    args = {'nombre': str(name), 'email': str(email), 'publicKey': pem_pu.decode('utf-8')}
    headers = {'Authorization': 'Bearer '+token}
    r = requests.post(url, headers=headers, json=args)

    if r.status_code != 200:
        print_error_server(r)
        return

    user = r.json()
    print('Identidad con ID#{0} creada correctamente'.format(user['userID']))
    return


def search_id(match):
    """ Search for matching users.
    Given a match string, looks for users with an username or email
    that contains the given string, and prints all the found users
    """
    # Create request
    url  = 'https://vega.ii.uam.es:8080/api/users/search'
    args = {'data_search': match}
    headers = {'Authorization': 'Bearer '+token}

    # Post request
    print('Buscando \'{0}\' en el servidor...'.format(match), end='', flush=True)
    r = requests.post(url, headers=headers, json=args)

    if r.status_code != 200 :
        print_error_server(r)
        return
    print('OK')

    # Print output
    users = r.json()
    print('{0} usuarios encontrados:'.format(len(users)))
    for index, user in enumerate(users):
        print("[{index}] {name}, {email}, ID: {id}".format(index=index, name=user['nombre'], email=user['email'], id=user['userID']))
    return


def delete_id(id):
    """ Deletes the user id from the server.
    Given the id, it tries to delete it from the server.
    Note that it is not possible to remove ids not associated to the
    current token (user)
    """
    # Create request
    url  = 'https://vega.ii.uam.es:8080/api/users/delete'
    args = {'userID': id}
    headers = {'Authorization': 'Bearer '+token}

    # Post request
    print('Solicitando borrado de la identidad #{0}...'.format(id), end='', flush=True)
    r = requests.post(url, headers=headers, json=args)

    if r.status_code != 200:
        print_error_server(r)
        return

    # Print output
    print('OK')
    print('Identidad con ID#{0} borrada correctamente'.format(id))
    return

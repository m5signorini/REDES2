"""
securebox_client
Contains the main functionality of the client
Authors:
    Ana Calzada
    Martin Sanchez
"""

import os
import sys
import argparse

import encryption
import id_management as idm
import file_management as flm

token = 'IMPORT TOKEN HERE'
user_data_dir = 'user-data/'
token_path = user_data_dir + 'token.txt'
private_key_path = user_data_dir + 'private_key.pem'


def create_user_data():
    """ Creates user-data directory.
    Creates the idrectory for storing all the data of the user,
    such as the API token or private keys
    """
    # Get directory path
    script_dir  = os.path.dirname(__file__)
    rel_path    = user_data_dir
    abs_path    = os.path.join(script_dir, rel_path)

    # Create directory
    try:
        os.makedirs(abs_path, exist_ok=True)
    except OSError:
        print ('Error: Could not create directory {0}'.format(abs_path))
        sys.exit(1)

    encryption.user_data_dir = user_data_dir
    encryption.private_key_path = private_key_path
    return


def load_token():
    """ Loads the API token.
    In order to access the API a token is needed.
    The token location is given in the token_path variable.
    The user must fill it before using the app.
    If no token is found, prompts the user to fill it,
    there after, it must be modified manually.
    """
    # Obtain paths for storing (relative to this script)
    script_dir  = os.path.dirname(__file__)
    rel_path    = token_path
    abs_path    = os.path.join(script_dir, rel_path)

    # Read from file
    try:
        f = open(abs_path, 'r')
        token = f.read().replace('\r','').replace('\n','')
        f.close()
    except FileNotFoundError:
        # Error: token file not found
        print('Error: Expected file {0} not found'.format(abs_path),file=sys.stderr)
        try:
            f = open(abs_path, 'w')
            f.close()
            print('File was created',file=sys.stderr)
            token = None
        except:
            print('Error: Could not create file {0}'.format(abs_path), file=sys.stderr)

    if not token:
        # Error: no token found
        print('Error: The file {0} must contain the raw token for the API'.format(abs_path),file=sys.stderr)
        print('Now you can introduce a token here that will be stored in said file',file=sys.stderr)
        print('  or leave it blank to close for now and fill it manually later',file=sys.stderr)

        # Prompt user for token
        token = input('Introduce API token: ')
        if not token:
            print('No token provided, fill the file {0} with the token'.format(abs_path),file=sys.stderr)
            return

        # Store token
        try:
            f = open(abs_path, 'w')
            f.write(token)
            f.close()
            print('Token succesfully stored')
        except:
            print('Error: Could not access file {0}'.format(abs_path), file=sys.stderr)

    # Load it in the rest of the scripts
    encryption.token = token
    idm.token = token
    flm.token = token
    return


def main():
    # Create parser
    parser = argparse.ArgumentParser(description="Programa para cifrar y firmar ficheros, subiendolos a un servidor gestionando a la vez un sistema de usuarios.")

    # User management
    parser.add_argument('--create_id',  dest='create_id',   action='store', nargs=2,    metavar=('name', 'email'),
                        help='Crea un nuevo id. Formato: --create_id Nombre Email')
    parser.add_argument('--search_id',  dest='search_id',   action='store', nargs=1,    metavar='cadena',
                        help='Busca una cadena entre los nombres y correos en el servidor, devolviendo sus correspondientes ids.')
    parser.add_argument('--delete_id',  dest='delete_id',   action='store', nargs=1,    metavar='userID',
                        help='Dado un id lo borra, solo es posible si pertenece al usuario actual.')
    # File management
    parser.add_argument('--upload',     dest='upload',      action='store', nargs=1,    metavar='fichero',
                        help='Firma y cifra un fichero y lo sube al servidor. Devuelve el id, necesario para la descarga. Hace falta especificar el destinatario.')
    parser.add_argument('--source_id',  dest='source_id',   action='store', nargs=1,    metavar='userID',
                        help='Define la id del usuario que subio un fichero, necesario para la descarga del dicho.')
    parser.add_argument('--dest_id',    dest='dest_id',     action='store', nargs=1,    metavar='userID',
                        help='Define la id del usuario que debe recibir el fichero, necesario para la subida del dicho.')
    parser.add_argument('--list_files', dest='list_files',  action='store_true',
                        help='Muestra todos los ficheros subidos por el actual usuario.')
    parser.add_argument('--download',   dest='download',    action='store', nargs=1,    metavar='fileID',
                        help='Dado el id de un fichero lo descarga, descifra y verifica la firma. Hace falta especificar la id del usuario que lo subió.')
    parser.add_argument('--delete_file',dest='delete_file', action='store', nargs=1,    metavar='fileID',
                        help='Borra el fichero con la id especificada, solo si lo subió el usuario actual.')
    # Crypto management
    parser.add_argument('--encrypt',    dest='encrypt',     action='store', nargs=1,    metavar='fichero',
                        help='Cifra en local el fichero especificado.')
    parser.add_argument('--sign',       dest='sign',        action='store', nargs=1,    metavar='fichero',
                        help='Firma en local el fichero especificado.')
    parser.add_argument('--enc_sign',   dest='enc_sign',    action='store', nargs=1,    metavar='fichero',
                        help='Firma y cifra en local el fichero especificado')

    # If no arguments, print help
    if len(sys.argv)==1:
        parser.print_help(sys.stderr)
        sys.exit(0)

    # Check arguments
    args = parser.parse_args()
    create_user_data()
    load_token()

    # ID MANAGEMENT
    if args.create_id:
        if   len(args.create_id) == 2:
            idm.create_id(args.create_id[0], args.create_id[1], None)
        else:
            # Print help on error
            print('Error: Incorrect number of arguments for --create_id, expected 2', file=sys.stderr)
            print('Usage: --create_id NAME EMAIL', file=sys.stderr)
            sys.exit(1)

    if args.search_id:
        idm.search_id(args.search_id[0])

    if args.delete_id:
        idm.delete_id(args.delete_id[0])

    # FILE MANAGEMENT
    if args.upload:
        if not args.dest_id:
            print('Error: Expected option --dest_id', file=sys.stderr)
            print('Usage: --upload FILE --dest_id userID', file=sys.stderr)
            sys.exit(1)
        flm.upload(args.upload[0], args.dest_id[0])

    if args.list_files:
        flm.list_files()

    if args.download:
        if not args.source_id:
            print('Error: Expected option --source_id', file=sys.stderr)
            print('Usage: --download FILE --source_id userID', file=sys.stderr)
            sys.exit(1)
        flm.download_file(args.download[0], args.source_id[0])

    if args.delete_file:
        flm.delete_file(args.delete_file[0])

    # ENCRYPTION
    if args.encrypt:
        if not args.dest_id:
            print('Error: Expected option --dest_id', file=sys.stderr)
            print('Usage: --encrypt FILE --dest_id userID', file=sys.stderr)
            sys.exit(1)
        encryption.generate_encrypted_file(file=args.encrypt[0], id=args.dest_id[0])

    if args.sign:
        encryption.generate_signed_file(file=args.sign[0])

    if args.enc_sign:
        if not args.dest_id:
            print('Error: Expected option --dest_id', file=sys.stderr)
            print('Usage: --enc_sign FILE --dest_id userID', file=sys.stderr)
            sys.exit(1)
        encryption.generate_encrypted_file(file=args.enc_sign[0], id=args.dest_id[0])

    return





if __name__ == "__main__":
    main()

"""
TODO:
    - More tests
    - More comments
    - Better tests
"""

from Cryptodome.Random import get_random_bytes
import os, sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import encryption

script_dir  = os.path.dirname(__file__)
test_data   = os.path.join(script_dir, 'test.dat')

def test_sign_data():
    """
    TEST: encryption.sign_data
    """
    # Create sample
    data = get_random_bytes(1024)
    key_pr, key_pu = encryption.generate_rsa_key()
    # Check signature
    signature, data = encryption.sign_data(data, key_pr)
    if encryption.verify_data(signature, data, key_pu):
        print('OK: test_sign_data')
    else:
        print('ERROR: test_sign_data')
    return


def test_sign_file():
    """
    TEST: encryption.generate_signed_file
    """
    # Create sample
    data = get_random_bytes(1024)
    key_pr, key_pu = encryption.generate_rsa_key()

    f = open(test_data, 'wb')
    f.write(data)
    f.close()

    out = encryption.get_signed_name(test_data)
    encryption.generate_signed_file(test_data, key_pr, out)
    if encryption.verify_file(out, key_pu):
        print('OK: test_sign_file')
    else:
        print('ERROR: test_sign_file')
    return


def test_encrypt_data():
    """
    TEST: encryption.encrypt_data
    """
    # Create sample
    data = get_random_bytes(256)
    key_pr, key_pu = encryption.generate_rsa_key()

    iv, enc_session_key, enc_data = encryption.encrypt_data(data, key_pu)
    dec_data = encryption.decrypt_data(iv, enc_session_key, enc_data, key_pr)
    if data == dec_data:
        print('OK: test_encrypt_data')
    else:
        print('ERROR: test_encrypt_data')
    return


def test_encrypt_file():
    """
    TEST: encryption.generate_encrypted_file
    """
    # Create sample
    data = get_random_bytes(1024)
    key_pr, key_pu = encryption.generate_rsa_key()

    f = open(test_data, 'wb')
    f.write(data)
    f.close()

    out = encryption.get_encrypted_name(test_data)
    encryption.generate_encrypted_file(test_data, key_pu, out)

    # Contrast data
    f = open(out, 'rb')
    iv, enc_session_key, enc_data = encryption.get_encrypted_components(f.read())
    f.close()

    dec_data = encryption.decrypt_data(iv, enc_session_key, enc_data, key_pr)
    if data == dec_data:
        print('OK: test_encrypt_file')
    else:
        print('ERRROR: test_encrypt_file')
    return


def test_sign_and_encrypt_file():
    """
    TEST: generate_encrypted_signed_file
    """
    # Sample
    data = get_random_bytes(1024)
    key_pr, key_pu = encryption.generate_rsa_key()

    f = open(test_data, 'wb')
    f.write(data)
    f.close()

    out = encryption.get_signed_name(test_data)
    out = encryption.get_encrypted_name(out)
    encryption.generate_encrypted_signed_file(test_data, key_pu=key_pu, key_pr=key_pr, output=out)

    if encryption.verify_encrypted_file(out, key_pr, key_pu) is True:
        print('OK: test_sign_and_encrypt_file')
    else:
        print('ERROR: test_sign_and_encrypt_file')


def test_store_key():
    """
    TEST: store_key, get_key
    """
    key_pr, key_pu = encryption.generate_rsa_key()
    encryption.store_key(key_pu, 'test/test_public_key.pem')
    encryption.store_key(key_pr, 'test/test_private_key.pem')

    st_key_pu = encryption.get_key('test/test_public_key.pem')
    st_key_pr = encryption.get_key('test/test_private_key.pem')

    if encryption.get_pem_format(key_pr) == encryption.get_pem_format(st_key_pr):
        if encryption.get_pem_format(key_pu) == encryption.get_pem_format(st_key_pu):
            print('OK: test_store_key')
            return
    print('ERROR: test_store_key')
    return


if __name__ == "__main__":
    test_sign_data()
    test_encrypt_data()
    test_sign_file()
    test_encrypt_file()
    test_sign_and_encrypt_file()
    test_store_key()

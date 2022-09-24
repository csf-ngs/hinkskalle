import struct
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.asymmetric.ec import EllipticCurvePublicKey

def get_public_key(key_data: bytes) -> EllipticCurvePublicKey:
    return load_der_public_key(key_data)

# shamelessly stolen from https://github.com/pyauth/pywarp/blob/master/pywarp/authenticators.py
class AuthenticatorData:
    def __init__(self, auth_data):
        self.raw_auth_data = auth_data
        self.rp_id_hash, flags, self.signature_counter = struct.unpack(">32s1sI", auth_data[:37])
        flags = [bool(int(i)) for i in format(ord(flags), "08b")]
        (self.extension_data_included,
         self.attested_credential_data_included, _, _, _,
         self.user_verified, _,
         self.user_present) = flags
        self.credential_id = None
        self.credential_public_key = None
        if self.attested_credential_data_included:
            aaguid, credential_id_length = struct.unpack(">16sH", auth_data[37:55])
            self.credential_id = auth_data[55:55 + credential_id_length]
            self.credential_public_key = auth_data[55 + credential_id_length:]
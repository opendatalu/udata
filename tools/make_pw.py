import hmac
import hashlib
import base64
import bcrypt


PASSWORD_SALT = "Default uData secret password salt"


def get_hmac(password: str | bytes) -> bytes:
    h = hmac.new(
        PASSWORD_SALT.encode("utf-8"), password.encode("utf-8"), hashlib.sha512
    )
    return base64.b64encode(h.digest())


def hash_password(password):
    """Hash the password using double hashing and bcrypt."""
    hmac_password = get_hmac(password)
    bcrypt_hash = bcrypt.hashpw(hmac_password, bcrypt.gensalt())
    return bcrypt_hash.decode("utf-8")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate a HMAC password")
    parser.add_argument("-p", help="The password to hash", required=True)
    args = parser.parse_args()

    print(hash_password(args.p))

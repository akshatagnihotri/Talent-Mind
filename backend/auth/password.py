"""
TalentMind AI — Password Utilities
Direct bcrypt-based password hashing and verification.
"""
import bcrypt


def hash_password(plain_password: str) -> str:
    """
    Return a bcrypt hash of ``plain_password``.

    Parameters
    ----------
    plain_password:
        The raw password string provided by the user.

    Returns
    -------
    str
        Bcrypt hash suitable for storage in the database.
    """
    password_bytes = plain_password.encode('utf-8')
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check ``plain_password`` against the stored bcrypt ``hashed_password``.

    Parameters
    ----------
    plain_password:
        The raw password string supplied at login time.
    hashed_password:
        The bcrypt hash retrieved from the database.

    Returns
    -------
    bool
        ``True`` if the password matches, ``False`` otherwise.
    """
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False

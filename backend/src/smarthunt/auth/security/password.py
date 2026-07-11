import bcrypt


def hash_password(password: str) -> str:
    """تشفير كلمة المرور وتحويل الـ bytes الناتجة إلى string متوافق مع الداتابيز"""
    password_bytes = password.encode("utf-8")
    # توليد الـ salt وعمل الـ hash بمعدل 12 rounds متوافق مع $2b$12$
    hashed = bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """التحقق من صحة كلمة المرور بمقارنة النص الصريح مع الـ Hash المشفر"""
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

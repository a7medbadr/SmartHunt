from smarthunt.auth.security.password import hash_password, verify_password

password = "my_secret_password"

# 1. عمل الـ Hash
hashed = hash_password(password)
print(hashed)

# 2. عمل الـ Verify
is_valid = verify_password(password, hashed)
print(is_valid)

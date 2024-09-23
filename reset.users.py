import json
import hashlib

# Funzione per generare l'hash della password
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Crea un nuovo dizionario con le credenziali predefinite
default_users = {
    "admin": hash_password("password")  # Username: admin, Password: password
}

# Salva il dizionario nel file users.json
with open('users.json', 'w') as f:
    json.dump(default_users, f)

print("Credenziali ripristinate: admin / password")

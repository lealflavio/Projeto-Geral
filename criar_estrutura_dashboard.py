import os

BASE_DIR = "/home/flavioleal_souza/Sistema/dashboard"

folders = [
    "backend/app/api",
    "backend/app/core",
    "backend/app/db",
    "backend/app/models",
    "backend/app/schemas",
    "backend/app/services",
    "backend/app/utils",
    "frontend/public",
    "frontend/src/assets",
    "frontend/src/components",
    "frontend/src/pages",
    "frontend/src/services",
    "frontend/src/styles",
]

for folder in folders:
    path = os.path.join(BASE_DIR, folder)
    os.makedirs(path, exist_ok=True)
    print(f"Criado: {path}")

print("Estrutura de pastas criada com sucesso.")

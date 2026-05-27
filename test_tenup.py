import requests

url = "https://tenup.fft.fr/tournoi/82173545"

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

response = requests.get(url, headers=headers)

print("Statut HTTP :", response.status_code)
print("Taille de la page :", len(response.text), "caractères")
print("---")
print("Aperçu :")
print(response.text[:800])

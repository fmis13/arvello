# Arvello

Arvello je cjelovito poslovno rješenje za hrvatsko tržište koje uključuje:
- Upravljanje računima i ponudama
- Evidenciju proizvoda i usluga
- Administraciju klijenata i dobavljača
- Obračun plaća i JOPPD izvještavanje
- Upravljanje inventarom
- Vođenje knjige ulaznih i izlaznih računa
- i još više...

## Sadržaj

- [Instalacija](#instalacija)
  - [Razvoj na lokalnom računalu](#razvoj-na-lokalnom-računalu)
  - [Produkcijsko okruženje](#produkcijsko-okruženje)
- [Korištenje](#korištenje)
- [Doprinošenje](#doprinošenje)
- [Licenca](#licenca)

## Instalacija

### Razvoj na lokalnom računalu

Za lokalni razvoj, slijedite ove korake:

```bash
# Instalirajte potrebne pakete
sudo apt install git-all ufw python3.11-venv

# Klonirajte repozitorij
git clone https://github.com/fmis13/arvello.git

# Stvorite virtualno okruženje
python3 -m venv /putanja/koju/zelite

# Aktivirajte virtualno okruženje
source /putanja/koju_ste/postavili/bin/activate

# Premjestite se u projektni direktorij
cd arvello

# Instalirajte ovisnosti
pip3 install -r requirements.txt

# Dopustite port kroz firewall (po potrebi)
sudo ufw allow [PORT]

# Pokrenite razvojni server
python manage.py runserver [IP ADRESA]:[PORT]
```

### Produkcijsko okruženje

Za postavljanje Arvella u produkcijskom okruženju, koristite automatiziranu skriptu:

#### Priprema

1. Osigurajte da koristite Debian ili Ubuntu distribuciju
2. Osigurajte da imate root pristup na serveru
3. Preuzmite deploy skriptu u svoj direktorij:

```bash
wget https://raw.githubusercontent.com/fmis13/arvello/main/deploy_arvello.sh
```

#### Pokretanje deploy skripte

1. Dodijelite izvršna prava skripti:

```bash
chmod +x deploy_arvello.sh
```

2. Pokrenite skriptu kao root korisnik:

```bash
sudo ./deploy_arvello.sh
```

3. Slijedite upute na zaslonu za unos potrebnih informacija:
   - Naziv domene (FQDN)
   - PostgreSQL podaci (naziv baze, korisničko ime, lozinka)
   - Django admin podaci (korisničko ime, lozinka)
   - Email postavke (poslužitelj, port, korisničko ime, lozinka)
   - HTTP port za Arvello aplikaciju

#### Nakon instalacije

Nakon završetka instalacije:
1. Arvello će biti dostupan na vašem serveru na konfiguriranom HTTP portu
2. Za javni pristup, koristite Nginx Proxy Manager za prosljeđivanje zahtjeva i SSL certifikat
3. Pristupite aplikaciji s admin vjerodajnicama koje ste postavili tijekom instalacije

## Korištenje

Nakon uspješne instalacije, možete pristupiti Arvellu putem web preglednika:
- Lokalni razvoj: http://localhost:8000/ (ili konfigurirani port)
- Produkcija: https://vasa-domena.com (nakon postavljanja Nginx Proxy Manager-a)

## Doprinošenje

Ako želite doprinijeti projektu, molimo pričekajte do kraja 6. mjeseca 2025.

## Licenca

Ovaj projekt je licenciran pod [MIT licencom](LICENSE).

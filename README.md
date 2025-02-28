# <center>**Arvello**</center>
# <center>**NOTE - THIS DOCUMENTATION IS A WIP!**</center>

A simple invoice creator for Croatian small businesses.
This program is written to adapt the Croatian language. Further adding of other functionality is imminent. 

## Table of Contents

- [Installation](#installation)
- [Contributing](#contributing)
- [License](#license)

## Installation

sudo apt install git-all ufw #instalirajte Git i ufw (firewall), python3 se uglavnom nalazi preinstaliran

git clone https://github.com/fmis13/arvello.git

sudo apt install python3.11-venv

python3 -m venv /putanja/koju/zelite

source /putanja/koju_ste/postavili/bin/activate

cd /putanja/u/koju/ste/pokrenuli-git-clone

pip3 install -r requirements.txt

cd arvello

sudo ufw allow [PORT] #dopuštavanje korištenja porta kroz firewall

python manage.py runserver [IP ADRESA]:[PORT] #ovime se pokreće web server

## Notes!
None for now.
## Contributing

Contributing will not be allowed until 13-06-2025 23:59 CET because of this project being a part of a national competition.
All pull requests until then ***will be rejected***.

## License

This project uses a MIT license. It can be found in the root folder by the file LICENSE. Please understand that you may be bound by other licenses from other projects used in this project, including, but not limited to:
GNU AGPL v3 for HUB-3 Barcode API

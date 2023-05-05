# LogBot

Discord bot, za logiranje ur...

### Proces zagona:

SHH to VM

(python3 -m venv venv)

source venv/bin/activate

python3 main.py  ali nohup python3 -u main.py &>> activity.log &


Potrebni paketi:
* pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
* pip install discord
* pip install datetime
* pip install oauth2client

## To do:
* dodaten kanal samo za testiranje,
* Urediti CGS problemi z izklaplanjem (https://www.digitalocean.com/community/tutorials/nohup-command-in-linux),
* Dodati ukaz za ročni zaklucek dneva,
* Hranjenje podatkov dneva v Sheets in ne v spremenljivki (Če  se program tekom dneva sesuje)

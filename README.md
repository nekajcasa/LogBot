# LogBot

Discord bot, za logiranje ur...

### Proces zagona:
<!--Do sedaj:
* SSH to VM
* (python3 -m venv venv)
* source venv/bin/activate
* python3 main.py  ali nohup python3 -u main.py &>> activity.log &

Na testu:-->
* SSH to VM
* source venv/bin/activate
* nohup python3 main.py &> output.txt &
* (cat output.txt)(za pregled output.txt)
* kill _ID_

Potrebni paketi:
* pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
* pip install discord
* pip install datetime
* pip install oauth2client

## To do:
* Hranjenje podatkov dneva v Sheets in ne v spremenljivki (Če  se program tekom dneva sesuje)
* možnost dodanjanja termina za en dan v naprej
<!-- 
* Urediti GCS problemi z izklaplanjem (https://www.digitalocean.com/community/tutorials/nohup-command-in-linux),
* Hranjenje e-mail naslovov v Sheets namesto v secrets
* avtomatski sestevek ur za mesec v sheet
-->

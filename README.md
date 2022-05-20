# groninger museum server

deze applicatie is bedoeld om de routes van de geleiden app op te slaan.


## prerequisits

om deze server te kunnen runnen moet je docker en docker compose geinstaleerd hebben

## start server
de eerste keer dat je deze server start moet je in de root van de applicatie het commando `docker-compose up --build -d` uitvoeren. dit commando die start de server en geeft daarna de terminal terug aan de gebruiker

### server stoppen
om de server te stoppen moet je in de root van de applicatie het command `docker-compose down` uitvoeren. om de server daarna weer te starten kan dat met het commando `docker-compose up -d` gebeuren 

## logs bekijken
om de logs van de server te bekijken kun je bij het opstarten van de server de tag `-d` weglaten of je kunt het commando `docker-compose logs` uitvoeren. als je wilt dat deze zelf updaten kun je de tag `-f` toevoegen. om niet alle lijnen te laten zien kun je de tag `--tail="{lijnen}"` toevoegen waarbij de textst `{lijnen}` het aantal gewenste lijnen is.

## developing
### python package toevoegen
om reen pytohn package toe te voegen moet je de naam ervan in het bestand `/flask/requirements.txt` toevoegen en de server opniuew opstarten met het commando `docker-compose up --build --force-recreate`.

### environment variablen toevoegen
om een environment variabele toe te voegen aan de python app moet je die in het bestand `/flask/.env` toevoegen. om deze in te laden moet je de applicatie handmatig opniew opstarten.

### bestanden vernieuwen
alle bestanden die in de folder `/flask/app` staan worden automatisch opnieuw geladen. las je een bestand buiten die volder aanpast dan moet je het zelfde commando als voor het toevoegen van een python package

### verbinden database 
je kunt met de databse verbinden via poort `3306` en host `database` verder staan de inloggevens in het bestand `docker-compose.yml` en `/flask/.env`

### database aanpassing
als je een aanpassing aan de databse wil doen die gedaan moet worden tijdens het opstarten kun je de query in het bestand `mysql/init.sql` toevoegen. om deze verandering door te laten gaan moeten de volgende commandos uitgevoerd worden.

```bash
$ docker-compose down
$ docker-compose rm
$ docker-compose up --build --force-recreate -d
```


## software
deze server maakt gebruik van een aantal verschiullende stukken software. hij maakt namelijk gebruik van 

 - nginx:latest
 - mariadb:latest
 - python:3.10



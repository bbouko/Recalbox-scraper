Recalbox-scraper
=====================
```
utilisation: scraper.py [-stats]

scraper pour Recalbox (EmulationStation)

arguments optionnels:
    
    -stats montre statisqtiques des jeux scrapés ou non

```

Script python qui permet de scraper les cover + infos du jeu et le sauvegarde en fichier XML compatible pour Recalbox (EmulationStation)

Utilisation
=====================

scrap avec le choix de la console en fonction des roms disponibles
```
$ python scrap.py
```

Retourne les statistiques d'un scrap (jeux scrapés + manquants)

```
$ python scrap.py -stats
```


Credits
=====================

ES-scraper : https://github.com/thadmiller/ES-scraper
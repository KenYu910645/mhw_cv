# mhw_cv
Steamwork bot and Auto-mining bot for MHW(Monster Hunter World)

## Demostration
BOT for steamwork mini-game
https://www.youtube.com/watch?v=nfppLuI6OaQ

Auto-mining BOT
https://www.youtube.com/watch?v=dw5GLl0rFBk

## Requirement
```
python 3.8.0
pip install Pillow opencv-python numpy pynput pypiwin32 pyinstaller
```
## Run auto steamwork bot
First, Execute your MHW, talk to steamwork NPC and press 'space' to start the steamwork game.
After that, execute command below to start this program.
Also make sure your screen focus is on MHW, otherwise it won't work.
```
python steamwork.py
```

## Run auto-mine dragonite bot

Frist, Execute your MHW and choose to go to explore in guiding land
Choose East camp(3) as start camp.
After that, adjust your camera orientation to make it face NORTH.(you can verify this by observe mini-map at left down corner)

Execute command below and you're good to go.
```
python mine_dragonite.py
```
Through out the mining process, always make sure your camera is facing NORTH, otherwise it will not work.
Currently, I don't have a way to deal with big monsters. They'll likely kill the character during the farming.Still, the bot know how to come back from the starting camp, so don't be too worry.

Press 'p' to start/pause the script

There're some equipment/jewels your should wear if you want ot farm effectively.
1. Intimidating III
    * Let mini monsters ignore you.
2. Geologist III
    * Allow you to mine 4 times and pick up bone 5 times.
3. Hunger Resistance III
    * Prevent the stamina debuff cause by starvation.
4. Master Gatherer I
    * Speed up the gathering animation.

## TODO 
* Add a auto-faceing north feature
* Wear an invisible cloak when big monsters are near.
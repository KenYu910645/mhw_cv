# mhw_cv
Auto-steamwork bot using computer vision

## Requirement
```
python 3.8.0
pip install PyDirectInput Pillow opencv-python numpy
```
## Run auto steamwork 
Execute your MHW, go to steamwork and press 'space' or 'R2' to start it.
After that, execute command down below to start auto-bot.
Also make sure your screen is focus on MHW, otherwise it won't work.
```
python steamwork.py
```

## Run auto dragonite

Execute your MHW, go exploring in guiding land and choose east camp(3).
After that, adjust your camera orientation to make it face NORTH.(you can verify this by observe mini-map at left down corner)

Execute command below and you're good to go.
```
python mine_dragonite.py
```
Through out the mining process, always make sure your camera is facing NORTH, otherwise it will go nuts.
Currently, I don't have way to deal with big monsters. Being killed is the best I can do for now. But the character know how to come back from the camp though, so don't worry.

There're some equipment/jewels your should wear if you wanna farm effectively.
1. Intimidating III
    Let the mini monster ignore you
2. Geologist III
    Allow you to mine 4 times and pick bone 5 times.
3. Hunger Resistance III
    Prevent you suffer from stamina debuff.


## TODO 
* Add a auto-faceing north feature
* Wear invisible cloak when monster is near.

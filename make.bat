pyinstaller --clean --noconfirm --onefile --distpath "./." --add-data "directkeys.py;." --hidden-import "pynput.keyboard._win32" --hidden-import "pynput.mouse._win32" "mine_dragonite.py"

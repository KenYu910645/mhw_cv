# -*- mode: python ; coding: utf-8 -*-

block_cipher = None


a = Analysis(['C:/Users/lucky/Desktop/mhw_cv/mine_dragonite.py'],
             pathex=['C:\\Users\\lucky\\Desktop\\mhw_cv'],
             binaries=[],
             datas=[('C:/Users/lucky/Desktop/mhw_cv/directkeys.py', '.')],
             hiddenimports=['pynput.keyboard._win32', 'pynput.mouse._win32'],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='mine_dragonite',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          upx_exclude=[],
          runtime_tmpdir=None,
          console=True )

import sys
sys.dont_write_bytecode = True
import PyInstaller.__main__
import os

base_path = os.path.abspath(os.path.dirname(__file__))

PyInstaller.__main__.run([
    'src/main.py',
    '--name=GestionFacturas',
    '--onefile',
    '--noconfirm',
    # Bundle src hierarchy and also map to root-level components/assets/etc for resolve_ui_path fallback
    '--add-data=src/components;src/components',
    '--add-data=src/components;components',
    '--add-data=src/assets;src/assets',
    '--add-data=src/assets;assets',
    '--add-data=src/models;src/models',
    '--add-data=src/models;models',
    '--add-data=src/config;src/config',
    '--add-data=src/config;config',
    '--add-data=src/utils;src/utils',
    '--add-data=src/utils;utils',
    '--hidden-import=PyQt6',
    '--hidden-import=sqlalchemy',
    '--hidden-import=models.usuario',
    '--hidden-import=config.database',
    '--hidden-import=utils.ui',
    '--hidden-import=components.usuario.login',
    '--hidden-import=components.main.main',
    '--path=.',
    '--windowed'
])
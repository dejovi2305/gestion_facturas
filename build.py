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
    '--add-data=src/components/usuario/login.ui;src/components/usuario',
    '--add-data=src/components/main/main.ui;src/components/main',
    '--add-data=src/assets;src/assets',
    '--add-data=src/models;src/models',
    '--add-data=src/config;src/config',
    '--add-data=src/components;src/components',
    '--hidden-import=PyQt6',
    '--hidden-import=sqlalchemy',
    '--hidden-import=models.usuario',
    '--hidden-import=config.database',
    '--hidden-import=components.usuario.login',
    '--hidden-import=components.main.main',
    '--path=.',
    '--windowed'
])
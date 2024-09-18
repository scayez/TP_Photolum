# INSTALLATION:
- Installer Anaconda
- Créer un environnement virtuel en python3.9 (par ex: py39):
  conda create --name py39 python=3.9
- Dans C:\...\anaconda3\envs\py39\Lib\site-packages\
  copier le fichier:
  pyBen.cp39-win_amd64.pyd
  et le dossier:
  pyBen-1.0.3-py3.9.egg-info
- Dans le dossier de travail (contenant le programme principal mesure_spectrale_v_xx.py)
  Copier les fichiers:  
  - benhw64.dll
  - System.atr
  - System.cfg
  - logo.png
  - Threads_init_acquire.py (les classes pour l'acquisition et l'initialisation du port série)
  - ui_photolum.ui (l'interface grfaphique utilisateur)
  - config.txt (les config de la liaison série)
- Les fichiers contenus dans [prolific_pl2303] windows usb serial adapter sont les drivers du câble d'adaptation USB/Série utilié pour le SR830.
  

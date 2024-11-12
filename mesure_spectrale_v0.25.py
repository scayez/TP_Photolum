"""
A FAIRE:
    - fonction auto_range pour changer automatiquement de gamme lors de la saturation en haut ou en bas
    l'ideal est de pouvoir activer/desactiver la fonction pendant la mesure.
    Pour teqster allumer ebn + le generateur de pulse pour la diode (+l'oscillo?)')


"""




import sys
from PyQt5 import QtWidgets, uic # utile pour utiliser les éléments de l’interface graphique  #QtCore,
from PyQt5.QtWidgets import QFileDialog
from Threads_init_acquire import MeasurementThread, ComPortThread
import numpy
import pyBen   # pour commander le monochromateur


qtCreatorFile = "ui_photolum.ui" #  fichier Interface Utilisateur 
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)



class MyWindow(QtWidgets.QMainWindow, Ui_MainWindow):   
    """
    Classe principale pour gérer la fenêtre de l'application et les différentes interactions avec l'utilisateur.
    """
    def __init__(self):     
        QtWidgets.QMainWindow.__init__(self)    # initialisation de l’IU
        Ui_MainWindow.__init__(self)
        super().__init__()
        self.setupUi(self)
        
        # Initialisation du thread de mesure
        self.measurement_thread = None
        self.donnees = None  # Attribut pour stocker les données de mesure
          
        # Gestion des boutons de l'interface utilisateur, l'action de cliquer sur un bouton active une fonction précise 
        self.pushButton_Initialisation.clicked.connect(self.initialisation)
        self.pushButton_Sauvegarder.clicked.connect(self.Sauvegarder)
        self.pushButton_Demarrer.clicked.connect(self.demarrer)
        self.pushButton_Stop.clicked.connect(self.stop)
        self.pushButton_Ordre0.clicked.connect(self.Ordre0)
        self.pushButton_Effacer.clicked.connect(self.Effacer)
        self.pushButton_cancel_init.clicked.connect(self.cancel_initialization)
        
        # Connecter les signaux valueChanged des widgets à la méthode calculate_duration
        self.spinBox_l_init.valueChanged.connect(self.calculate_duration)
        self.spinBox_l_final.valueChanged.connect(self.calculate_duration)
        #self.doubleSpinBox_pas.valueChanged.connect(self.calculate_duration)
        self.Slider_pas.valueChanged.connect(self.calculate_duration)
        self.spinBox_delay.valueChanged.connect(self.calculate_duration)
        
        self.progressBar.hide()
        
        # Initialisation du graph, definition de la couleur de fond, du titre, du titre des axes, de la grille pour chaque graph
        self.GW_R.setBackground('w')
        self.GW_R.setTitle("R")
        self.GW_R.setLabel('left', 'Intensité', color='red', size=30)
        self.GW_R.setLabel('bottom', 'Longueur d’onde (nm)', color='blue', size=30)
        self.GW_R.showGrid(x=True, y=True)         
        
        self.GW_theta.setBackground('w')
        self.GW_theta.setTitle("Theta")
        self.GW_theta.setLabel('left', 'Angle', color='red', size=30)
        self.GW_theta.setLabel('bottom', 'Longueur d’onde (nm)', color='blue', size=30)
        self.GW_theta.showGrid(x=True, y=True)
         
        # Gestion du spinbox qui permet à l'utilisateur de sélectionner le pas entre chaque mesure
        self.Slider_pas.valueChanged.connect(self.choix_pas)
        # Gestion du label de sauvegarde, il est caché au début
        self.label_sauvegarde.hide()
       
        #Spin box délai entre 2 points
        self.spinBox_delay.valueChanged.connect(self.update_delay)
        self.delay = self.spinBox_delay.value()
        
        # Récupérer les paramètres de mesure
        self.l_init = self.spinBox_l_init.value()
        self.l_final = self.spinBox_l_final.value()
        self.pas = self.Slider_pas.value()
        
        # self.pas = self.Slider_pas.value()
        
        # Calcul du nombre total de points de mesure
        self.total_points = int((self.l_final - self.l_init) / self.pas) + 1
        

        #♣read config file
        self.config = self.read_config('config.txt')
        print(self.config)
        
        #display the default duration
        self.calculate_duration()
        
        self.radioButton_autorange.toggled.connect(self.toggle_autorange)######################
        self.radioButton_autorange.setVisible(False)######################
     
  
    def read_config(self,file_path):
        config = {}
        with open(file_path, 'r') as file:
            for line in file:
                key, value = line.strip().split('=')
                config[key.strip()] = value.strip()
        return config
  
    def initialisation(self):
       """Initializes communication with the detection system and monochromator."""
       self.pushButton_Initialisation.setEnabled(False)
       self.label_Initialisation_SR830.setStyleSheet("color: orange;")
       self.label_Initialisation_SR830.setText("Initialisation en cours")
       
       
    
       # Create and start the COM port worker thread
       self.com_port_thread = ComPortThread(
        port=self.config['Port'],
        bitrate=int(self.config['BitRate']),
        timeout=float(self.config['Timeout'])
        )
       
       self.com_port_thread.initialization_success.connect(self.on_com_port_success)
       self.com_port_thread.initialization_failed.connect(self.on_com_port_failure)
       self.com_port_thread.start()

       # Initialize the monochromator
       self.label_initialisation_spectro.setStyleSheet("color: orange;")
       self.label_initialisation_spectro.setText("Initialisation en cours")
     
       erreur_init = pyBen.build_system_model("system.cfg").get('Error')
       erreur_init += pyBen.load_setup("system.atr").get('Error')
       erreur_init += pyBen.initialise().get('Error')
       erreur_init += pyBen.park().get('Error')
       pyBen.select_wavelength(0,0)  # Set monochromator to zero order

       if erreur_init != 0:
           self.label_initialisation_spectro.setStyleSheet("color: red;")
           self.label_initialisation_spectro.setText("Erreur d’initialisation TMc300")
           self.pushButton_Demarrer.setEnabled(False)
           self.pushButton_Stop.setEnabled(False)
           self.pushButton_Ordre0.setEnabled(False)
        
       else:
           self.label_initialisation_spectro.setStyleSheet("color: green;")
           self.label_initialisation_spectro.setText("TMc300 Initialisé")
           if self.label_Initialisation_SR830.text() == 'SR830 Initialisé':
               self.pushButton_Demarrer.setEnabled(True)
               self.pushButton_Stop.setEnabled(True)
               self.pushButton_Ordre0.setEnabled(True)
               self.pushButton_cancel_init.setEnabled(False)
               self.pushButton_Initialisation.setEnabled(False)

    def on_com_port_success(self, message):
       """Slot for handling successful COM port initialization."""
       self.label_Initialisation_SR830.setStyleSheet("color: green;")
       self.label_Initialisation_SR830.setText(message)
       # Assign the serial object from the worker to the main window
       self.ser = self.com_port_thread.ser
       if self.label_initialisation_spectro.text() == 'TMc300 Initialisé':
           self.pushButton_Demarrer.setEnabled(True)
           self.pushButton_Stop.setEnabled(True)
           self.pushButton_Ordre0.setEnabled(True)
           self.pushButton_cancel_init.setEnabled(False)
           self.pushButton_Initialisation.setEnabled(False)
       

    def on_com_port_failure(self, message):
        """Slot for handling failed COM port initialization."""
        self.label_Initialisation_SR830.setText(message)
        self.label_Initialisation_SR830.setStyleSheet("color: red;")
        self.pushButton_Demarrer.setEnabled(False)  # Disable start if COM initialization failed
        self.pushButton_Stop.setEnabled(False)
        self.pushButton_Ordre0.setEnabled(False)
    
    def cancel_initialization(self):
        """Stops the COM port initialization process."""
        if hasattr(self, 'com_port_thread'):
            self.com_port_thread.stop()  # Stop the  thread
        self.pushButton_Demarrer.setEnabled(False)
        self.pushButton_Stop.setEnabled(False)
        self.pushButton_Ordre0.setEnabled(False)
        self.pushButton_Initialisation.setEnabled(True)
        self.label_Initialisation_SR830.setText("Initialisation annulée")
        self.label_Initialisation_SR830.setStyleSheet("color: red;")
         
    def Ordre0(self):
        """Ramène le monochromateur à l'ordre 0."""
        pyBen.select_wavelength(0,0)
           
    def choix_pas(self):
        """Affiche la valeur actuelle du pas sélectionnée via le slider."""

        self.pas = self.Slider_pas.value()
        self.label_slider_pas.setText(str(self.pas))
       
    def demarrer(self):
        """Démarre le processus de mesure en lançant un thread."""
        # Configuration initiale
        self.pushButton_Demarrer.setEnabled(False)
        self.pushButton_Effacer.setEnabled(False)
        self.pushButton_Sauvegarder.setEnabled(False)
        self.spinBox_l_init.setEnabled(False)
        self.spinBox_l_final.setEnabled(False)
        self.Slider_pas.setEnabled(False)
        self.label_sauvegarde.hide()
        self.progressBar.show()
        
        delay = self.delay
        
        # Configurer les axes des graphiques
        R_X = self.comboBox_RX.currentText()
        if R_X == "R":
            self.ser.write(b'DDEF 1 {,1,0}\n')
            self.GW_R.setTitle("R")
        else:
            self.ser.write(b'DDEF 1 {,0,0}\n')
            self.GW_R.setTitle("X")
        
        self.Th_Y = self.comboBox_ThY.currentText()
        if self.Th_Y == "Theta":
            self.ser.write(b'DDEF 2 {,1,0}\n')
            self.GW_theta.setTitle("Theta")
            self.nb_carac = 9
        else:
            self.ser.write(b'DDEF 2 {,0,0}\n')
            self.GW_theta.setTitle("Y")
            self.nb_carac = 13

        # Démarrer le thread de mesure
        self.measurement_thread = MeasurementThread(self.ser, pyBen, self.l_init, self.l_final, self.pas, self.nb_carac, delay)
        self.measurement_thread.update_plot_R.connect(self.update_plot_R)
        self.measurement_thread.update_plot_Theta.connect(self.update_plot_Theta)
        self.measurement_thread.measurement_done.connect(self.on_measurement_done)
        self.measurement_thread.start()


    def update_plot_R(self, x_data, y_data):
        """Met à jour le graphique R avec les nouvelles données."""
        self.GW_R.clear()
        self.GW_R.plot(x_data, y_data, pen='r', symbol='o', symbolSize=2 ,symbolBrush='r',symbolPen='r')
        # Mise à jour de la barre de progression
        # Calculer le pourcentage de progression
        progress_percentage = int((len(x_data) / self.total_points) * 100)
        self.progressBar.setValue(progress_percentage)

    def update_plot_Theta(self, x_data, y_data):
        """Met à jour le graphique Theta avec les nouvelles données."""
        self.GW_theta.clear()
        self.GW_theta.plot(x_data, y_data, pen='b', symbol='o', symbolSize=2 ,symbolBrush='b',symbolPen='b')
        
    def update_delay(self):
        """Met à jour le délai sélectionné par l'utilisateur."""
        self.delay = self.spinBox_delay.value()
        
    def calculate_duration(self):
        self.l_init = self.spinBox_l_init.value()
        self.l_final = self.spinBox_l_final.value()
        self.pas = self.Slider_pas.value()
        self.delay = self.spinBox_delay.value()
        self.total_points = int((self.l_final - self.l_init) / self.pas) + 1
       
        reponse = float(self.config['Computer_response']) #temps d'acquisition sans délai
        self.duration = (self.total_points*((self.delay/1000)+reponse)) 
        self.duration = round(self.duration,1)
               
        # Convert the float duration (in seconds) to minutes and seconds
        minutes = int(self.duration // 60)
        seconds = int(self.duration % 60)
        
        # Format the duration as mm:ss
        formatted_time = f"{minutes:02}min {seconds:02}s"
        self.label_total_time.setText(str(formatted_time))



    def on_measurement_done(self,donnees):
        """Fonction appelée lorsque la mesure est terminée."""
        self.donnees = donnees  # Stocker les données reçues
        self.pushButton_Demarrer.setEnabled(True)
        self.pushButton_Sauvegarder.setEnabled(True)
        self.comboBox_RX.setEnabled(True)
        self.comboBox_ThY.setEnabled(True)
        self.spinBox_l_init.setEnabled(True)
        self.spinBox_l_final.setEnabled(True)
        self.Slider_pas.setEnabled(True)
        self.pushButton_Effacer.setEnabled(True)
        self.progressBar.hide()
        self.Sauvegarder()
        

    def stop(self):
        """Arrête la mesure en cours."""
        
        if self.measurement_thread is not None:  # Vérifier si le thread de mesure existe
            self.measurement_thread.arret_mesure = True  # Met à jour la variable dans le thread

        
    def Sauvegarder(self): #sauvegarde en tableau de texte séparé par un espace et à la ligne et affichage de la confirmation de la sauvegarde
       """Ouvre une fenêtre de dialogue pour sauvegarder le fichier"""
       options = QFileDialog.Options()
       options |= QFileDialog.DontUseNativeDialog
       default_path = "C:/Users/tp_tp4/Documents/"
       file_name, _ = QFileDialog.getSaveFileName(self, "Sauvegarder les données", default_path, "Text Files (*.txt);;All Files (*)", options=options)
    
       if file_name:
           # Sauvegarde des données dans le fichier sélectionné
           numpy.savetxt(file_name, self.donnees.transpose(), delimiter=' ', newline='\n')
           self.label_sauvegarde.setText(f"Fichier sauvegardé : {file_name}")
           self.label_sauvegarde.show()
    
    def Effacer(self): 
        """efface les graphs et ré-initialise le tableau données"""
        self.GW_R.clear()
        self.GW_theta.clear()
        self.donnees = numpy.empty((3, 1), numpy.float64)
        
 
        
    # Méthode pour gérer l'événement de fermeture de la fenêtre
    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question(self, 'Quitter', 
            "Êtes-vous sûr de vouloir quitter ?", QtWidgets.QMessageBox.Yes | 
            QtWidgets.QMessageBox.No, QtWidgets.QMessageBox.No)

        if reply == QtWidgets.QMessageBox.Yes:
            if self.ser.is_open:  # Vérifie si le port COM est ouvert
                self.ser.close()  # Ferme la communication série
                
            self.stop()# arrêtre l'acquisition si il y en a une en cours
            event.accept()
        else:
            event.ignore()
    ################################################################################################  
    def toggle_autorange(self, checked):#######################################################  
        """
        Called when the state of radioButton_autorange is changed.#######################################################  
        """
        if checked:
            self.measurement_thread.auto_range_enabled = True#######################################################  
        else:
            self.measurement_thread.auto_range_enabled = False#######################################################  
     ################################################################################################     
        
  
        
    #Cette fonction permettant d’avoir un réglage automatique de la sensibilité n’est pas terminée par manque de temps.
    #Au-delà de son fonctionnement qui est sûrement à améliorer (si le bruit est trop variable comment faire ?),
    #il est possible que rajouter de la communication avec la détection synchrone ralentisse la boucle encore plus
    """
    def auto_range(self):
        self.range = [2*10**-15, 5*10**-15, 10*10**-15, 20*10**-15, 50*10**-15,100*10**-15, 200*10**-15, 500*10**-15, 1*10**-12, 2*10**-12, 5*10**-12, 10*10**-12, 20*10**-12, 50*10**-12, 100*10**-12, 200*10**-12, 500*10**-12, 1*10**-9, 2*10**-9, 5*10**-9, 10*10**-9, 20*10**-9, 50*10**-9, 100*10**-9, 200*10**-9, 500*10**-9, 1*10**-6]
        increment = 0   #l’increment permet de changer la valeur de self.sensi pour la prochaine mesure
        if self.donnees[1,self.i] >= 0.9*self.range[self.sensi]:
            self.ser.write(b'SENS {%d}\n' %(self.sensi+1))
            increment = 1
        elif self.donnees[1,self.i] <= 0.1*self.range[self.sensi]:
            self.ser.write(b'SENS {%d}\n' %(self.sensi-1))
            increment = -1
        self.sensi = self.sensi + increment"""


if __name__ == "__main__": 
    app = QtWidgets.QApplication(sys.argv)
    window = MyWindow()
    window.show()
    sys.exit(app.exec_())

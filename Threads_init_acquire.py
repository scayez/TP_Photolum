from PyQt5.QtCore import QThread, pyqtSignal
import numpy
import serial   # pour la communication avec la detection synchrone
from serial.serialutil import SerialException


class MeasurementThread(QThread):
    """
    Thread pour gérer la mesure. Il communique avec l'interface utilisateur
    en émettant des signaux pour mettre à jour les graphiques en temps réel.
    """
    # Signaux pour communiquer avec l'interface principale
    update_plot_R = pyqtSignal(list, list)  # Signal pour mettre à jour le graphique R
    update_plot_Theta = pyqtSignal(list, list)  # Signal pour mettre à jour le graphique Theta
    measurement_done = pyqtSignal(numpy.ndarray)  # Signal pour indiquer que la mesure est terminée avec les données acquises

    def __init__(self, ser, pyBen, l_init, l_final, pas, nb_carac,delay):
        super().__init__()
        self.ser = ser
        self.pyBen = pyBen
        self.l_init = l_init
        self.l_final = l_final
        self.pas = pas
        self.nb_carac = nb_carac
        self.delay = delay
        self.donnees = numpy.empty((3, int((l_final - l_init) / pas) + 1), numpy.float64)
        self.i = 0
        self.l_mesure = l_init
        self.arret_mesure = False
        self.range = [2*10**-15, 5*10**-15, 10*10**-15, 20*10**-15, 50*10**-15,100*10**-15, 200*10**-15, 500*10**-15, 1*10**-12, 2*10**-12, 5*10**-12, 10*10**-12, 20*10**-12, 50*10**-12, 100*10**-12, 200*10**-12, 500*10**-12, 1*10**-9, 2*10**-9, 5*10**-9, 10*10**-9, 20*10**-9, 50*10**-9, 100*10**-9, 200*10**-9, 500*10**-9, 1*10**-6]
        self.sensi = 0  # Initial sensitivity index
        
    def auto_range(self):
        """
        Ajuste la sensibilité en fonction des données mesurées.

        """
        
        #self.ser.write(b'SENS {%d}\n' %5)
        self.ser.write(b'SENS {26}\n')
        print('---->'+str(self.ser.read(100)))
        
        # self.ser.write(b'AGAN\n')
        # self.ser.write(b'SENS {%d}\n' % (20))
        # print(b'SENS {%d}\n' % (20))
        
        # increment = 0
        # if self.donnees[1, self.i] >= 0.9 * self.range[self.sensi]:
        #     if self.sensi < len(self.range) - 1:
        #         self.ser.write(b'SENS {%d}\n' % (self.sensi + 1))
        #         increment = 1
        # elif self.donnees[1, self.i] <= 0.1 * self.range[self.sensi]:
        #     if self.sensi > 0:
        #         self.ser.write(b'SENS {%d}\n' % (self.sensi - 1))
        #         increment = -1
        # self.sensi += increment
        #print(self.sensi)
    def run(self):
        """
        Fonction principale du thread pour effectuer les mesures à chaque pas
        et mettre à jour les graphiques correspondants.
        """
        while not self.arret_mesure and self.l_mesure <= self.l_final:
            # Positionner le Monochromateur à la longueur d'onde l_mesure
            erreur_wave = self.pyBen.select_wavelength(self.l_mesure, 0).get('Error')
            if erreur_wave != 0:
                self.arret_mesure = True
                break
            # Compléter le tableau
            self.donnees[0, self.i] = self.l_mesure
            self.ser.write(b'OUTR ? 1\n')
            self.donnees[1, self.i] = float(self.ser.read(20))
            self.ser.write(b'OUTR ? 2\n')
            self.donnees[2, self.i] = float(self.ser.read(self.nb_carac))

            # Émettre un signal pour mettre à jour le graphique R
            self.update_plot_R.emit(self.donnees[0, :self.i + 1].tolist(), self.donnees[1, :self.i + 1].tolist())
            
            # Appeler la fonction auto_range pour ajuster la sensibilité!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
            self.auto_range()

            # Émettre un signal pour mettre à jour le graphique Theta
            self.update_plot_Theta.emit(self.donnees[0, :self.i + 1].tolist(), self.donnees[2, :self.i + 1].tolist())

            QThread.msleep(self.delay)
            # Incrémenter la longueur d'onde
            self.l_mesure += self.pas
            self.i += 1
        # Émettre un signal pour indiquer que la mesure est terminée
        self.measurement_done.emit(self.donnees)
  
        
class ComPortThread(QThread):
    """
    Worker thread to handle opening the COM port.
    Emits signals to indicate success or failure.
    """
    initialization_success = pyqtSignal(str)  # Signal for successful initialization
    initialization_failed = pyqtSignal(str)   # Signal for failed initialization

    def __init__(self, port, bitrate, timeout, parent=None):
        super().__init__(parent)
        self.port = port
        self.bitrate = bitrate
        self.timeout = timeout
    
    def run(self):
        try:
            # Attempt to open the COM port
            self.ser = serial.Serial(
                self.port,
                self.bitrate,
                bytesize=serial.EIGHTBITS,
                timeout=self.timeout,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                rtscts=True
            )
            # Send a test command and read the response
            self.ser.write(b'*IDN?\n')
            sortie = self.ser.read(100)
            if not sortie:
                raise SerialException("No response from device.")
            nom = str(sortie).split("'")[1].split()[0].split(",")[1]

            # Emit success signal
            self.initialization_success.emit(nom + " Initialisé")
        except SerialException as e:
            # Emit failure signal with detailed error
            self.initialization_failed.emit(f"SerialException: {str(e)}")
        except Exception as e:
            # Emit failure signal with generic error
            self.initialization_failed.emit(f"Exception: {str(e)}")

        
    def stop(self):
        """Request the thread to stop running."""
        self._stop_requested = True
        if hasattr(self, 'ser') and self.ser.is_open:
            self.ser.close()
        
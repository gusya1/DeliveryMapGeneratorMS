
from PyQt5 import QtWidgets
import sys
from mainwindow import MainWindow
from geogenerator import MapGenerator, MapGeneratorError
from MSApi import MSApi


def fatal_error(message):
    QtWidgets.QMessageBox.critical(None, "Error", str(message))
    app.exit(1)
    exit()


try:
    from settings import *
except ImportError:
    fatal_error("settings.py not found")


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    try:
        MSApi.set_access_token(MOY_SKLAD.TOKEN)

        MapGenerator.set_googlemap_key(GOOGLEMAPS_SETTINGS.AUCH_KEY)
        MapGenerator.projects_blacklist = MOY_SKLAD.PROJECTS_BLACKLIST

    except MapGeneratorError as e:
        fatal_error(e)

    window = MainWindow()
    window.show()
    app.exec()

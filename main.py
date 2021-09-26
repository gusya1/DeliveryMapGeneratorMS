
from PyQt5 import QtWidgets
import sys
import configparser


from mainwindow import MainWindow
from geogenerator import MapGenerator, MapGeneratorError


def fatal_error(message):
    QtWidgets.QMessageBox.critical(None, "Error", str(message))
    app.exit(1)
    exit()


if __name__ == '__main__':

    app = QtWidgets.QApplication(sys.argv)

    if len(app.arguments()) != 2:
        fatal_error("Invalid arguments.\nUsage: python3 MapGenerator <settings_file>")

    config_path = app.arguments()[1]

    try:
        open(config_path, 'r')
    except FileNotFoundError as e:
        fatal_error(e)

    config = configparser.ConfigParser()
    config.read(config_path, encoding="utf-8")

    try:
        MapGenerator.moy_sklad_login(config['moy_sklad']['login'],
                                     config['moy_sklad']['password'])
        MapGenerator.set_googlemap_key(config['googlemaps']['key'])
        MapGenerator.projects_blacklist = config['moy_sklad']['projects_blacklist'].split(",")
    except KeyError as e:
        fatal_error(f"Settings parameter {e} not found")
    except MapGeneratorError as e:
        fatal_error(e)

    window = MainWindow()
    window.show()
    app.exec()

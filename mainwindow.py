from PyQt5 import uic, QtWidgets, QtCore
from PyQt5.QtWidgets import QMainWindow
# from PyQt5 import QtGui
# from PyQt5.QtPrintSupport import QPrinter, QPrintDialog
# from PyQt5.QtCore import QMarginsF
from geogenerator import MapGenerator, MapGeneratorError

class MainWindow(QMainWindow):

    def __error(self, err):
        QtWidgets.QMessageBox.critical(self, "Error", str(err))

    def __init__(self, parent=None):
        super().__init__(parent)
        uic.loadUi("mainwindow.ui", self)

        self.map_generator = MapGenerator()

        self.btnGenerate.clicked.connect(self.on_btnGenerateClicked)

        self.download_location = QtCore.QStandardPaths.writableLocation(
            QtCore.QStandardPaths.StandardLocation.DownloadLocation)

    @QtCore.pyqtSlot()
    def on_btnGenerateClicked(self):
        date = self.calendarWidget.selectedDate().toPyDate()
        try:
            total_count, success_count, geojson = self.map_generator.create_map_for_day(date)

            if len(self.map_generator.get_error_list()) != 0:
                error_list = ""
                for i, error in enumerate(self.map_generator.get_error_list()):
                    error_list += f"<li><b>[{i}]</b> {error}</li>"
                QtWidgets.QMessageBox.critical(self, f"{len(self.map_generator.get_error_list())} Errors", error_list)

            if total_count == 0:
                QtWidgets.QMessageBox.warning(self, "Warning", "Customerorder not found")
                return

            if success_count == 0:
                QtWidgets.QMessageBox.warning(self, "Warning", f"All customerorder failed {success_count}/{total_count}")
                return

            try:
                file = open(f"{self.download_location}/GeoMap_{date.strftime('%Y-%m-%d')}.geojson", 'w')
                file.write(geojson)
                file.close()
            except OSError as e:
                self.__error(e)
            else:
                QtWidgets.QMessageBox.information(self, "Success", f"{success_count}/{total_count}")
        except MapGeneratorError as e:
            QtWidgets.QMessageBox.critical(self, "Error", str(e))




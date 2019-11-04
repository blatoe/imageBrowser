import os
import sys



dir = os.path.dirname(__file__)
sys.path.append(dir)
sys.path.append(dir+'/external')
import ui
from PySide2 import QtWidgets
app = QtWidgets.QApplication(sys.argv)
a = ui.ImageBrowser(dir + '/_test')

sys.exit(app.exec_())
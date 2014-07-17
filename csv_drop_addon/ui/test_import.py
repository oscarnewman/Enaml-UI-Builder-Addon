import traits_enaml

from pyface.api import FileDialog, OK  
from csv_import_options import CSVImportOptions
from enaml.qt.qt_application import QtApplication

if __name__ == "__main__":
    with traits_enaml.imports():
        from csv_import_view import CSVImportView

    dialog = FileDialog(wildcard='*.csv')
    if dialog.open() == OK:

	    opts = CSVImportOptions()
	    opts.path = dialog.path

	    app = QtApplication()

	    view = CSVImportView(options = opts)
	    view.show()

	    app.start()
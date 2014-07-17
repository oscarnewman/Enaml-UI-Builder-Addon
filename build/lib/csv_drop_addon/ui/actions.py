import traits_enaml
from enaml.qt.qt_application import QtApplication
from pyface.tasks.action.api import GroupSchema, MenuSchema, ActionSchema, \
    TaskAction
from pyface.api import ConfirmationDialog, FileDialog, \
    YES, OK, CANCEL

from csv_import_options import CSVImportOptions

FILE_HANDLING_SERVICE = 'canopy.file_handling.i_file_handling_service.IFileHandlingService'

# Code definitions

class OpenDataFileAction(TaskAction):
    """ Open a data file containing a table/array (ex: CSV). """

    name = 'Import Table to UI Builder...'
    id = 'OpenDataFileAction'
    tooltip = 'Import Table to UI Builder...'

    def perform(self, event):
        dialog = FileDialog(wildcard='*.csv')
        if dialog.open() == OK:

            with traits_enaml.imports():
                from csv_drop_addon.ui.csv_import_view import CSVImportView

            opts = CSVImportOptions()
            opts.path = dialog.path

            app = QtApplication()

            view = CSVImportView(options = opts)
            view.show()

            app.start()


        

action_schema =  ActionSchema(
    action_factory = OpenDataFileAction,
    id = 'OpenDataFileAction'
)

menu_group_schema = MenuSchema(
    # 'Create' group.
    ActionSchema(
        action_factory = OpenDataFileAction,
        id = 'OpenDataFileAction'
    ),
    id='CreateCSVGroup',
)
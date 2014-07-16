from pyface.tasks.action.api import GroupSchema, MenuSchema, ActionSchema, \
    TaskAction
from traits.api import Str, on_trait_change
import traitsui
from pyface.api import ConfirmationDialog, FileDialog, \
    YES, OK, CANCEL

from csv_drop_addon.ui.csv_options import CSVOptions


FILE_HANDLING_SERVICE = 'canopy.file_handling.i_file_handling_service.IFileHandlingService'

# Code definitions

class OpenDataFileAction(TaskAction):
    """ Open a data file containing a table/array (ex: CSV). """

    name = '&Load Pandas DataFrame...'
    id = 'OpenDataFileAction'
    tooltip = 'Load Pandas DataFrame...'

    def perform(self, event):

        dialog = FileDialog(wildcard='*.csv')
        if dialog.open() == OK:
            optionWindow = CSVOptions(path=dialog.path)
            optionWindow.configure_traits()


        

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
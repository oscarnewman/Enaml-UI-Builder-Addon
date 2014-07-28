from pkg_resources import resource_filename
import os.path

import traits_enaml
from enaml.qt.qt_application import QtApplication
from pyface.tasks.action.api import GroupSchema, MenuSchema, ActionSchema, \
    TaskAction
from pyface.action.api import Action
from pyface.api import ConfirmationDialog, FileDialog, \
    YES, OK, CANCEL
from canopy.file_handling.i_file_handling_service import IFileHandlingService
import table_import


class OpenTableAction(TaskAction):

    """ Open a table in the UI builder from a file. Meant to be inherited from. 
    """

    file_types = {
        'All files (*)' : '*'
    }

    file_type_name = "File"
    name = 'Import DataFrame...'
    tooltip = name
    id = 'OpenTableAction'

    def perform(self, event):
        app = event.task.window.application
        service = app.get_service(IFileHandlingService)
        directory = service.get_recent_directory()

        dialog = FileDialog(
            wildcard=self._wildcard_string(), default_directory=directory)
        dialog.title = 'Load Table to UI Builder'
        if dialog.open() == OK:
            service.push_recent_file(dialog.path)
            table_import.run(dialog.path, app.home)

    def _wildcard_string(self):
        wildcard = ""
        for key in self.file_types:
            wildcard += key + "|"
            wildcard += self.file_types[key] + "|"
        return wildcard[:-1]




menu_group_schema = ActionSchema(
    action_factory=OpenTableAction,
    id='OpenTableAction',
)
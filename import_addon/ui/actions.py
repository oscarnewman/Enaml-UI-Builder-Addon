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

import logging

class OpenTableAction(TaskAction):

    """ Open a table in the UI builder from a file. Meant to be inherited from. 
    """

    file_types = {
        'All files (*)' : '*'
    }

    name = 'Import DataFrame...'
    tooltip = name
    id = 'OpenTableAction'

    def perform(self, event):
        app = event.task.window.application
        service = app.get_service(IFileHandlingService)
        directory = service.get_recent_directory()

        dialog = FileDialog(
            wildcard=self._wildcard_string(), default_directory=directory)
        dialog.title = 'Import DataFrame from File'
        if dialog.open() == OK:
            service.push_recent_file(dialog.path)
            # table_import.run(dialog.path, app.home)
            code_task = app.get_task('canopy.integrated_code_editor')
            code =\
"""
def callback(df):
    # print 'DataFrame saved as `df`'
    globals()['df'] = df
"""

            code += "import table_import\n"
            code += "table_import.run('"+dialog.path+"','"+app.home+"',callback)"
            code += "\nprint '\\n\\ndataframe will be saved as `df`'" 

            # Run the code in the frontend
            code_task.python_pane.frontend.execute_command(code)


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
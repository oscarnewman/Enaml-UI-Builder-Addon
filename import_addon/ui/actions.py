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

import application_manager

class OpenTableAction(TaskAction):

    """ Open a table in the UI builder from a file. Meant to be inherited from. 
    """

    file_types = {
        'All files (*)' : '*'
    }

    file_type_name = "File"
    name = 'Import DataFrame From File...'
    tooltip = name
    id = 'OpenFileAction'

    def perform(self, event):
        app = event.task.window.application
        service = app.get_service(IFileHandlingService)
        directory = service.get_recent_directory()

        dialog = FileDialog(
            wildcard=self._wildcard_string(), default_directory=directory)
        dialog.title = 'Load Table to UI Builder'
        if dialog.open() == OK:
            ext = os.path.splitext(dialog.path)[1]
            self.extension = ext
            service.push_recent_file(dialog.path)

            opts = self._get_model(dialog.path)
            opts.path = dialog.path
            opts.application = app
            opts.save_dir = app.home

            application_manager.create_app()

            view = self._get_enaml_view(dialog.path)
            view.options = opts
            view.show()

    def _get_enaml_view(self, path):
        raise NotImplementedError('Enaml View Not Defined')

    def _get_model(self, path):
        raise NotImplementedError('Model Not Defined')

    def _wildcard_string(self):
        wildcard = ""
        for key in self.file_types:
            wildcard += key + "|"
            wildcard += self.file_types[key] + "|"
        return wildcard[:-1]


class OpenDelimFixedAction(OpenTableAction):
    """ Open a Delimted or Fixed Width file. """

    file_type_name = "All"
    file_types = {
        'All Files(*)': '*',
    }

    name = 'Import DataFrame...'
    tooltip = name
    id = 'OpenDelimFixedAction'

    xl = ['.xls', '.xlsx']


    def _get_enaml_view(self, path):
        if self.extension.lower() in self.xl:
            with traits_enaml.imports():
                from excel_import_view import ExcelImportView
            return ExcelImportView()

        with traits_enaml.imports():
                from delim_fixed_import_view import DelimFixedImportView
        return DelimFixedImportView()

    def _get_model(self, path):
        if self.extension.lower() in self.xl:
            from excel_import_options import ExcelImportOptions
            return ExcelImportOptions()

        from delim_fixed_import_options import DelimFixedImportOptions
        return DelimFixedImportOptions()

class OpenFWFAction(OpenTableAction):
    """ Open a Fixed Width file. """

    file_type_name = "Fixed Width File"
    file_types = {
        'All files (*)' : '*',
    }

    name = 'Fixed Width File'
    tooltip = name
    id = 'OpenFWFAction'

    def _get_enaml_view(self):
        with traits_enaml.imports():
                from fwf_import_view import FWFImportView
        return FWFImportView()

    def _get_model(self):
        from fwf_import_options import FWFImportOptions
        return FWFImportOptions()

class OpenExcelAction(OpenTableAction):
    """ Open a Fixed Width file. """

    file_type_name = "Excel"
    file_types = {
        'Excel Files (*.xls)' : '*.xls',
    }

    name = 'Excel'
    tooltip = name
    id = 'OpenExcelAction'

    def _get_enaml_view(self):
        with traits_enaml.imports():
                from excel_import_view import ExcelImportView
        return ExcelImportView()

    def _get_model(self):
        from excel_import_options import ExcelImportOptions
        return ExcelImportOptions()



menu_group_schema = ActionSchema(
    action_factory=OpenDelimFixedAction,
    id='OpenDelimFixedAction',
    name = 'Import Dataframe...'
)
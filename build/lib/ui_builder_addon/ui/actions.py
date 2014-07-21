from pkg_resources import resource_filename

import traits_enaml
from enaml.qt.qt_application import QtApplication
from pyface.tasks.action.api import GroupSchema, MenuSchema, ActionSchema, \
    TaskAction
from pyface.action.api import Action
from pyface.api import ConfirmationDialog, FileDialog, \
    YES, OK, CANCEL
from canopy.file_handling.i_file_handling_service import IFileHandlingService
from enaml_ui_builder import run

import application_manager


def create_activate_task_action_factory(task_id, name, image=None):

    def activate_task_action_factory(**traits):
        """ Create an action that activates a task. """

        def perform():
            # the app itself will be launched in its original location
            # (not the egg)
            with traits_enaml.imports():
                from misc_views import DialogPopup
            application_manager.create_app()
            dialog = DialogPopup()
            dialog.show()
            run()
            dialog.close()

        return Action(on_perform=perform, name=name, image=image)

    return activate_task_action_factory


class OpenTableAction(TaskAction):

    """ Open a table in the UI builder from a file. Meant to be inherited from. 
    """

    file_types = {
        'All files' : '*'
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
            
            service.push_recent_file(dialog.path)

            opts = self._get_model()
            opts.path = dialog.path

            application_manager.create_app()

            view = self._get_enaml_view()
            view.options = opts
            view.show()

    def _get_enaml_view(self):
        raise NotImplementedError('Enaml View Not Defined')

    def _get_model(self):
        raise NotImplementedError('Model Not Defined')

    def _wildcard_string(self):
        wildcard = ""
        for key in self.file_types:
            wildcard += key + "|"
            wildcard += self.file_types[key] + "|"
        return wildcard[:-1]


class OpenCSVAction(OpenTableAction):
    """ Open a CSV file. """

    file_type_name = "CSV"
    file_types = {
        'CSV Files (*.csv)': '*.csv',
    }

    name = 'Import DataFrame From CSV...'
    tooltip = name
    id = 'OpenCSVAction'

    def _get_enaml_view(self):
        with traits_enaml.imports():
                from csv_import_view import CSVImportView
        return CSVImportView()

    def _get_model(self):
        from csv_import_options import CSVImportOptions
        return CSVImportOptions()

class OpenFWFAction(OpenTableAction):
    """ Open a Fixed Width file. """

    file_type_name = "Fixed Width File"
    file_types = {
        'All files (*)' : '*',
    }

    name = 'Import DataFrame From Fixed Width File...'
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
        'Excel Files (*.xls, *.xlsx)' : '*.xls,*.xlsx',
    }

    name = 'Import DataFrame From Excel File...'
    tooltip = name
    id = 'OpenExcelAction'

    def _get_enaml_view(self):
        with traits_enaml.imports():
                from excel_import_view import ExcelImportView
        return ExcelImportView()

    def _get_model(self):
        from excel_import_options import ExcelImportOptions
        return ExcelImportOptions()

menu_group_schema = MenuSchema(
    ActionSchema(
        action_factory=OpenCSVAction,
        id='OpenCSVAction'
    ),
    ActionSchema(
        action_factory=OpenFWFAction,
        id='OpenFWFAction'
    ),
    ActionSchema(
        action_factory=OpenExcelAction,
        id='OpenExcelAction'
    ),
    id='CreateCSVGroup',
    name='Enaml UI Builder'
)

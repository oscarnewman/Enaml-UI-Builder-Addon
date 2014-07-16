""" Allows for Canopy to open CSV files in the Enaml UI Builder """

from envisage.api import Plugin
from envisage.ui.tasks.api import TaskExtension
from traits.api import List
from canopy.file_handling.file_type import FileType


class CSVDropPlugin(Plugin):
    """ Allows for Canopy to open CSV files in the Enaml UI Builder """

    # Extension point IDs.
    LANGUAGES = 'canopy.code_editor.languages'
    EDITOR_FACTORIES  = 'canopy.code_editor.editor_factories'
    TASK_EXTENSIONS = 'envisage.ui.tasks.task_extensions'

    # Unique ID for this Plugin.
    id = 'csv_drop'

    # User-readable name for this Plugin.
    name = 'CSV Drop Plugin'

    #### Contributions to extension points made by this plugin ################

    task_extensions = List(contributes_to=TASK_EXTENSIONS)

    def _task_extensions_default(self):
        from pyface.tasks.action.api import SchemaAddition
        from csv_drop_addon.ui.actions import action_schema


        extension = TaskExtension(
            # extends only the code editor task
            task_id='canopy.integrated_code_editor',
            #before='View',
            # List of factories that return dock pane instances.
            #dock_pane_factories = [self._create_hello_world_dock_pane]
            actions=[ SchemaAddition(
                path='MenuBar/File',
                after="SaveGroup",
                before="PrintGroup",
                factory=lambda : action_schema,
                id='csv_drop'),
            ],
        )

        return [extension]

    # Editor Factor for drag/drop of CSV 
    # (Likely to be removed in favor of menu item)

    editor_factories = List(contributes_to=EDITOR_FACTORIES)

    def _editor_factories_default(self):
        from csv_drop_addon.csv_editor_factory import CSVEditorFactory
        from csv_drop_addon.csv_editor import CSVEditor

        fileTypeCSV = FileType()
        fileTypeCSV.name = 'CSV'
        fileTypeCSV.extensions = ['*.csv', '.csv']

        file_types = [fileTypeCSV]

        factory = CSVEditorFactory(file_types=file_types,
                                   schemes=['file', ''])

        return [factory]
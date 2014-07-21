""" Allows for Canopy to open CSV files in the Enaml UI Builder """

from envisage.api import Plugin
from envisage.ui.tasks.api import TaskExtension
from traits.api import List
from canopy.file_handling.file_type import FileType


class UIBuilderPlugin(Plugin):
    """ Allows for Canopy to open CSV files in the Enaml UI Builder """

    # Extension point IDs.
    TASK_EXTENSIONS = 'envisage.ui.tasks.task_extensions'

    # Unique ID for this Plugin.
    id = 'builder_addon'

    # User-readable name for this Plugin.
    name = 'Enaml UI Builder'

    #### Contributions to extension points made by this plugin ################

    task_extensions = List(contributes_to=TASK_EXTENSIONS)

    def _task_extensions_default(self):
        from pyface.tasks.action.api import SchemaAddition
        from ui_builder_addon.ui.actions import action_schema

        menu_extension = TaskExtension(
            task_id='canopy.integrated_code_editor',
            actions=[ SchemaAddition(
                path='MenuBar/File',
                after="SaveGroup",
                before="PrintGroup",
                factory=lambda : action_schema,
                id='csv_drop'),
            ],
        )

        return [menu_extension]

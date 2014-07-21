""" Allows Canopy to open CSV files in the Enaml UI Builder """
from pkg_resources import resource_filename

import traits_enaml
from envisage.api import Plugin
from envisage.ui.tasks.api import TaskExtension
from traits.api import List
from pyface.action.api import Action
from pyface.tasks.action.api import SchemaAddition
from enaml_ui_builder import run

from ui_builder_addon.ui import application_manager

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
        from ui_builder_addon.ui.actions import menu_group_schema, \
            create_activate_task_action_factory

        image_fname = resource_filename('builder_addon',
                                        'img/addon.png')

        activate_portfolio_task_factory = \
            create_activate_task_action_factory(
                task_id='enaml_ui_builder',
                name='Enaml UI Builder',
                image=image_fname,
            )

        activate_portfolio_task_addition = SchemaAddition(
            id='ActivateUIBuilderAction',
            path='WelcomeApps',
            factory=activate_portfolio_task_factory,
        )

        welcome_extension = TaskExtension(
            # Contribute the extension to this task.
            task_id='canopy.welcome',
            actions=[activate_portfolio_task_addition]
        )


        menu_extension = TaskExtension(
            task_id='canopy.integrated_code_editor',
            actions=[ SchemaAddition(
                path='MenuBar/File',
                after="SaveGroup",
                before="PrintGroup",
                factory=lambda : menu_group_schema,
                id='csv_drop'),
            ],
        )

        return [menu_extension, welcome_extension]

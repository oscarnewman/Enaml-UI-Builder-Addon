# Canopy product code
#
# (C) Copyright 2011 Enthought, Inc., Austin, TX
# All right reserved.
#
# This file is confidential and NOT open source.  Do not distribute.
#

# System library imports
import os.path

# Enthought library imports.
from traits.api import Str, List, ListStr

# Local imports.
from canopy.util.urls import get_parsed_url, get_local_path
from canopy.editor.url_editor_factory import URLEditorFactory
from canopy.file_handling.file_type import FileType
from pyface.api import MessageDialog, YES


################################################################################
# `CodeEditorFactory` class.
################################################################################
class CSVEditorFactory(URLEditorFactory):

    # User visible name of the factory
    name = Str('CSV Editor')

    # id of the factory
    id = Str('csv_drop.csv_editor')

    ####### 'IEditorFactory' interface. ########################################

    def get_editor(self, obj, task, **info):
        """ Return an editor suitable for the object `obj`.
        """
        from apptools.io.api import File
        from csv_drop_addon.csv_editor import CSVEditor

        # We pop out the line, and column values from info, because the file is
        # lazy-loaded, not yet loaded, when a CodeEditor is instantiated.
        line = info.pop('line', 0)
        column = info.pop('column', 0)

        parsed = get_parsed_url(obj)
        # Create the editor or get an existing editor.
        if parsed.scheme not in ('','file'):
            return False

        path = get_local_path(parsed)
        editor = CSVEditor()
        editor.obj = File(path)

        dialog = MessageDialog(severity="warning",
            title="CSVEditorFactory",
            message="Working.")
        dialog.open()

        return editor

    def create_new(self, editor_type=None, task=None, **info):
        """ Return a new/empty editor of the specified type. """
        # XXX: task is always a CodeEditor task?
        lang_name = 'CSV' if editor_type is None else editor_type
        app = task.window.application
        languages = app.get_extensions('canopy.code_editor.languages')
        for language in languages:
            if language.name == lang_name:
                break
        return self.get_editor('', task, **dict(language=language, **info))

    ####### Private  interface. ###############################################

    def _is_editor_usable(self, editor):
        """ Returns whether the specified editor can be used to open a file.
        """
        return (editor.obj is None or not editor.obj.path) and not editor.text



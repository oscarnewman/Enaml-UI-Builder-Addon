# Standard library imports.
from contextlib import contextmanager
from os.path import (basename, dirname, exists, join,
        isfile, splitext)
from os import linesep
import logging
import string
from StringIO import StringIO
import tokenize
import re

# System library imports.
from canopy.util.api import Promise
from pyface.qt import QtGui

# Enthought library imports.
from apptools.io.api import File
from pyface.api import MessageDialog, ConfirmationDialog, YES, NO, CANCEL
from pyface.timer.api import do_later
from traits.api import Bool, Instance, Int, Property, String, List, Unicode, \
    implements, on_trait_change, cached_property

# Local imports
from canopy.scripting.api import recordable
from canopy.file_handling.i_file_handling_service import IFileHandlingService
from canopy.code_tools.api import ICodeHelper, CodeHelperService
from canopy.editor.i_file_editor import IFileEditor
from canopy.code_editor.languages.api import PythonHelper
from canopy.editor.common_editor_actions import SaveAction
from canopy.code_editor.widget.file_system_watcher import FileSystemWatcher
from canopy.code_editor.base_code_editor import BaseCodeEditor

# Logging.
logger = logging.getLogger(__name__)

###############################################################################
# Classes.
###############################################################################

class CSVEditor(BaseCodeEditor):
    """ A code editor that operates on CSV Files.
    """
    implements(IFileEditor)

    #### 'IEditor' interface ##################################################

    obj = Instance(File)
    tooltip = Property(Unicode, depends_on='obj.path')

    #### 'CodeEditor' interface ###############################################

    # The encoding of the file.
    encoding = String('ascii')

    # Flag indicating whether the most last load was performed successfully.
    loaded = Bool(False)

    # The code editor status manager. This will be obtained at runtime from the
    # task if it is available.
    status_widget = Instance(
        'canopy.code_editor.widget.status_widget.CodeEditorStatusWidget')

    # Flag indicating if tab completion is enabled or not.
    tab_completion_enabled = Bool(False)

    # Flag indicating if smart parenthesis is enabled or not
    smart_parenthesis_enabled = Bool(False)

    # Flag indication code warnings
    code_warnings = List()

    # Whether occurrences of symbol under cursor should be highlighted.
    highlight_occurrences_enabled = Bool(False)

    # Strip whitespaces on save
    strip_whitespace = Bool(False)

    #### Private traits #######################################################

    # Code helper service
    code_helper = Property(Instance(ICodeHelper),
                            depends_on=['language', 'editor_area'])

    # Flag to indicate that a save process is taking place
    # This is used to skip reload notification on when saving file
    _in_save = Bool(False)

    # Create a file watcher
    _watcher = Instance(FileSystemWatcher)

    # The line ending style of the file.  The file's line ending style is
    # detected when opening it and preserved when saving it.  If initial line
    # ending style is mixed, the platform default is used consistently.
    _linesep = String(linesep)

    # Hash of the file when it was last loaded into the buffer
    _file_hash = String

    # Hash of the current text in the editor
    _text_hash = Property(String, depends_on=['text'])

    # Promise objects which notify of updates to tooltip.
    _tooltip_parts = List

    # The id and pos of the last shown tooltip, used to update its content.
    _last_tooltip_id = Int
    _last_tooltip_pos = Int

    ###########################################################################
    # 'IEditor' interface.
    ###########################################################################

    # def _handle_csv_drop(self, event):
    #     self.cursor.write(str(event.data.get_data('text/csv')))

    # def _on_drag_event(self, event):
    #     """ Handle python code drop events by the editor itself. File drop events
    #     are handled by the editor area.
    #     """
    #     mimedata = event.data
    #     if not mimedata:
    #         return
    #     elif mimedata.hasFormat('text/csv'):
    #         event.set_drop_handler(self._handle_csv_drop)


    def create(self, parent):
        """ Reimplemented to connect our status bar, if available.
        """
        super(CSVEditor, self).create(parent)
        self.status_widget = self._create_status_widget()
        if self.status_widget:
            languages = sorted([language.name for language in self.languages])
            self.status_widget.languages = languages
            if self.is_active:
                self.status_widget.current_language = self.language.name
        self.font = self.editor_area.task.window.application.font
        if self.obj != self._obj_default():
            self._obj_changed(self._obj_default(), self.obj)
        # Clear the undo-available for undoing to empty file content
        self.code_widget.setUndoRedoEnabled(False)
        self.code_widget.setUndoRedoEnabled(True)
        self.code_widget.smart_paren_closing = self.smart_parenthesis_enabled

    def destroy(self):
        """ Reimplemented to disconnect our status bar, if necessary.
        """
        # Prevent status bar line/column trait handlers from firing after the
        # code widget has been destroyed.
        self.status_widget = None

        # Prevent watching for files we don't have open anymore
        path = self.obj.absolute_path
        if path and path in self._watcher.files():
            self._watcher.remove_path(path)
        self._watcher = None

        super(CSVEditor, self).destroy()

    ###########################################################################
    # 'IFileEditor' interface.
    ###########################################################################

    @recordable
    def save(self, filename=None):
        """ Save the open file. Opens the save_as() dialog if no path is set.

        If `filename` is specified, the file is saved under that path
        instead of obj.path. This behaves like save_as() but without changing
        the editor's obj.path or modification state.
        """

        # If the file has not yet been saved then prompt for the file name.
        if len(self.obj.path) == 0 and filename is None:
            self.save_as()
        else:
            self._in_save = True

            if self.strip_whitespace:
                text = self._strip_whitespace().replace('\n', self._linesep)
            else:
                text = self.text.replace('\n', self._linesep)

            if filename is None:
                saved_code, self.encoding, self._file_hash = self.language.save(
                                            self.obj.path, text, self.encoding)
            else:
                saved_code, _, _ = self.language.save(filename, text,
                                                      self.encoding)
            saved_code = saved_code.replace(self._linesep, '\n')
            if saved_code != self.text:
                with self._keep_cursor_position():
                    self.text = saved_code
            if filename is None:
                self.reset_modifications()
            self._in_save = False

    @recordable
    def save_as(self, name=''):
        """ Save the file under a new path by showing a file selection dialog.
        """
        filename = self._get_save_file_name(name, self.language, True)
        if not filename:
            return False

        self.name = basename(filename)
        if self.obj.absolute_path:
            old_filename = self.obj.path
        else:
            old_filename = None
        self.obj.path = filename
        self._path_changed(old_filename, filename)

        # Change language according to the new extension
        ext = splitext(filename)[-1]
        if ext not in self.language.extensions:
            language = None
            for lang in self.languages:
                if ext in lang.extensions:
                    language = lang
                    break
            # Unknown extension, assign Plain text
            if not language:
                name = 'Plain Text'
                for lang in self.languages:
                    if lang.name == name:
                        language = lang
                        break
            # If Plain text is not there - give up, keep the previous
            if language:
                self.language = language

        app = self.editor_area.task.window.application
        file_handling_service = app.get_service(IFileHandlingService)
        file_handling_service.push_recent_file(self.obj.path)
        self.save()
        return True

    def load(self):
        loaded = False
        try:
            path = self.obj.path
            code, self.encoding, self._linesep, self._file_hash = self.language.load(path)
            self._original_text = code
            self.text = code
            self.reset_modifications()
            loaded = True
            if self.obj.absolute_path not in self._watcher.files():
                self._watcher.add_path(self.obj.absolute_path)
        finally:
            self.loaded = loaded

    @recordable
    def revert(self):
        # FIXME: Document exact behavior, especially with respect to save file,
        # and compared to reload.
        self.text = self._original_text
        self.reset_modifications()

    @recordable
    def reload(self):
        path = self.obj.path
        if len(path) != 0 and exists(path):
            with self._keep_cursor_position():
                code, self.encoding, self._linesep, self._file_hash = \
                    self.language.load(path)
                self.text = code
                self.reset_modifications()

    def revert_reload(self):
        if self._before_reload:
            self.select_all()
            self.cursor.write(self._before_reload)

    #### Public methods #######################################################

    def ensure_saved(self, message):
        """ Try to ensure that the file has been saved.

        Returns True if the file is saved.
        May pop-up confirmation/save-as/error dialogs as appropriate.

        """
        if len(self.obj.path) == 0 or self.dirty:
            dialog = ConfirmationDialog(
                parent=self.control,
                title="Confirm",
                message=message,
                informative="Do you want to save the file?",
                cancel=False, default=YES,
                yes_label = "Save", no_label="Cancel")
            result = dialog.open()
            if result != YES:
                return False
            try:
                if len(self.obj.path) > 0:
                    self.save()
                else:
                    return self.save_as()
            except Exception as exc:
                dialog = MessageDialog(
                    parent=self.control,
                    severity='error',
                    title='Error saving file',
                    message="Error while saving file '%s'." % self.obj.path,
                    detail=str(exc),
                )
                return False
        return len(self.obj.path) > 0 and not self.dirty


    #### Code assistance functions ############################################

    def tab_complete(self):
        """Perform tab completion. Return True if this was successful.
        """
        if not self.tab_completion_enabled:
            return False

        service = self.code_helper
        if service is None:
            return False

        # Do not tab_complete if code_widget cursor has selection.
        if self.code_widget.textCursor().hasSelection():
            return False

        source = self.text
        line, col = self.cursor.line() + 1, self.cursor.column()

        # FIXME: Language specific things should go into language helpers.
        try:
            for token in tokenize.generate_tokens(StringIO(source).readline):
                if token[2] > (line, col):
                    break
                elif (line, col) <= token[3] and \
                    token[0] in (tokenize.COMMENT, tokenize.STRING):
                    return False
        except Exception:
            pass

        root, fname = self._get_project_path()
        pos = self.cursor.position()

        block_text = self.code_widget.textCursor().block().text()
        # Complete "from canopy <tab>" to "from canopy import "
        if block_text.lstrip().startswith('from '):
            match = re.match(r'\s*from\s+\S+\s+(\S+)?$', block_text[:col])
            if match:
                import_group = match.groups()[-1] or ''
                if 'import'.startswith(import_group):
                    self.cursor.write('import '[len(import_group):])
                    return True

        # Don't complete on whitespace, except in import statement.
        # i.e. "from canopy import <tab>" should do tab-completion.
        if block_text == '' or col == 0 or (
                col > 0 and block_text[col-1] in string.whitespace and
                not re.match(r'\s*(from\s+\S+\s+)?(import|from) .*$', block_text[:col])):
            return False

        # Docstring display if we are near a (.
        fragment = source[pos-2:pos+1]
        if '(' in fragment:
            bracket_location = fragment.find('(')
            doc_pos = pos -1 + bracket_location
            doc = service.get_docstring(root, source, doc_pos, fname)
            if len(doc) > 0:
                self.code_widget.show_tip(doc)
            return True

        # Otherwise, try and complete.
        partial, completions = service.code_complete(root, source, pos, fname)
        if len(completions) > 0:
            if len(completions) == 1:
                self.cursor.write(completions[0][len(partial):])
            else:
                self.code_widget.show_completion(completions, partial)
        return True

    def show_tooltip(self, pos, selection=''):
        """ Show tooltip for given position.
        """
        if self.code_helper:
            source = self.text
            root, fname = self._get_project_path()
            tooltips = self.code_helper.get_tooltip(root, source, pos, fname,
                                                    selection)
            self._tooltip_parts = tooltips
            self._last_tooltip_pos = pos
            if len(tooltips) > 0:
                self._show_current_tooltip_text(pos, update=False)
                return True
            else:
                self._last_tooltip_id = 0
        return False

    def goto_definition(self):
        """ Go to the definition of the symbol under the cursor.
        """
        service = self.code_helper
        if service is None:
            return False

        source = self.text
        pos = self.cursor.position()
        root, fname = self._get_project_path()
        path, line, column = service.get_location(root, source, pos, fname)

        column += 1 # column numbers are 1-indexed.
        if path == self.obj.path:
            self.goto_line(line)
            self.goto_column(column)
            return True
        elif path:
            app = self.editor_area.task.window.application
            file_handling_service = app.get_service(IFileHandlingService)
            file_handling_service.open_file(path, line=line, column=column)
            return True
        else:
            return False

    ###########################################################################
    # 'ICanopyEditor' interface.
    ###########################################################################
    def get_editor_args(self):
        """ Return arguments to restore the editor to the current state. """
        return [self.obj.path, dict(line=self.line,
                                    column=self.column,
                                    factory_id=self.id)]

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_status_widget(self):
        from canopy.code_editor.widget.status_widget import CodeEditorStatusWidget
        status_widget = CodeEditorStatusWidget()
        status_widget._create()
        return status_widget

    def _confirm_close(self):
        """ Prompt the user to save their changes, if necessary.
        """
        if self.dirty:
            dialog = ConfirmationDialog(
                parent=self.control,
                title="Confirm",
                message="The file has been modified.",
                informative="Do you want to save the changes you made in " \
                    "'%s'?" % self.name,
                cancel=True, default=YES,
                yes_label = "Save", no_label="Don't Save")
            result = dialog.open()
            if result == CANCEL:
                return False
            elif result == YES:
                # FIXME: we need to have a flag for save vs. save as.
                try:
                    if len(self.obj.path) > 0:
                        self.save()
                    else:
                        return self.save_as()
                except Exception, exc:
                    dialog = ConfirmationDialog(
                        parent=self.control,
                        message="Error while saving file '%s'." % self.obj.path,
                        informative="Do you want to close the file anyway?",
                        detail=str(exc),
                        default=NO,
                        yes_label = "Close", no_label="Don't Close")
                    result = dialog.open()
                    if result == NO:
                        return False
        return True

    def _notify_external_change(self, change=None):
        """ Notify/hide notification about external change to file.

        `change` specifies the widget to show (hide others) or False to hide all
        info widgets or None to hide all except reload_ask_widget.
        Currently defined widgets are:
          reload_ask - ask user to reload the file content on external change
                  when file buffer is dirty
          reload_info - inform user that file has been reloaded on an
                  external change when file buffer is unmodified
          delete_notify - notify user that file has been deleted from disk

        """
        widgets = ['reload_info', 'reload_ask', 'delete_notify',
                   'chars_replaced']
        show = [False] * len(widgets)
        if change is None:
            # No need to hide reload_info even if no change has happened
            del widgets[0]
        elif change != False:
            show[widgets.index(change)] = True
        acw = self._advanced_code_widget
        for i, widget_name in enumerate(widgets):
            getattr(acw, widget_name+'_widget').setVisible(show[i])

    def _check_modified(self):
        """ Check if the file has been really modified underneath.
        """
        if self.obj.path == '' or self.code_widget is None or self._destroyed:
            # nothing to do here
            return
        if isfile(self.obj.path):
            _, _, _, new_hash = self.language.load(self.obj.path)
            if self._file_hash != new_hash:
                if self.dirty:
                    self._notify_external_change('reload_ask')
                else:
                    self._before_reload = self.text
                    self.reload()
                    self._notify_external_change('reload_info')
            elif self._text_hash == new_hash:
                self.reset_modifications()
                self._notify_external_change(None)
        else:
            self.dirty = True
            self._notify_external_change('delete_notify')

    def _get_save_file_name(self, hint_path=None, language=None,
                            add_default_extension=True):
        """ Return a file path suitable as name for a new file.
        hint_path can be used to give hint for default directory,
        and language is used for dialog file filters.
        If add_default_extension is True, a default extension is added
        to filename based on the language if the user did specify an extension
        neither changed the language extension filter.
        """
        if not hint_path:
            hint_path = self.obj.absolute_path if self.obj.path else ''
        if language is None:
            language = self.language
        extensions = language.extensions

        # Get save directory and extension
        if hint_path:
            ext = splitext(hint_path)[-1]
            directory = hint_path
        else:
            ext = extensions[0] if len(extensions) > 0 else None
            app = self.editor_area.task.window.application
            file_handling_service = app.get_service(IFileHandlingService)
            directory = join(file_handling_service.get_recent_directory())

        # Build the filter
        language_filter = language.name + \
                                ' (*' + ' *'.join(extensions) + ')'
        filters = language_filter + ';;All files (*)'

        filename, selected_filter = QtGui.QFileDialog.getSaveFileName(
            self.control.window(), caption="Save As...", dir=directory,
            filter=filters, selectedFilter=language_filter)

        if filename and add_default_extension and \
                not splitext(filename)[1] and \
                selected_filter == language_filter and \
                ext is not None:
            # Add the default extension in case no extension is added by
            # user. The default extension is the same as existing file's
            # extension if any, else the selected language's first extension
            filename += ext

        return filename

    def _get_project_path(self):
        """ Return a project path and file name suitable for supplement. """
        # Try and determine the filename and project root directory.
        if len(self.obj.path) == 0:
            return '', ''
        else:
            pth = f_pth = self.obj.absolute_path
            pth = dirname(pth)
            while True:
                if exists(join(dirname(pth), '__init__.py')):
                    pth = dirname(pth)
                else:
                    break
            return pth, f_pth

    def _strip_whitespace(self):
        """ Strips off extraneous whitespace, and ensures linebreak at EOF

        NOTE: self.text has only \n characters for line-breaks.
        """

        stripped_text = re.sub('[ \t\v\f\r]+\n', '\n', self.text).rstrip()
        return stripped_text + '\n'

    @contextmanager
    def _keep_cursor_position(self):
        # Save the cursor and scroll position
        line, column = self.code_widget.get_line_column()
        v, h = self.code_widget.get_vertical_horizontal_scroll()
        try:
            yield
        finally:
            # Go back to the old cursor and scroll position
            self.code_widget.set_line_column(line, column)
            self.code_widget.set_vertical_horizontal_scroll(v, h)

    ####### Signal handlers ###################################################

    @on_trait_change('_watcher:file_changed')
    def _file_change(self, path):
        # File watcher is shared by multiple editors
        if self.obj.path != path:
            # nothing to do here
            return

        if not self._in_save:
            do_later(self._check_modified)

    @on_trait_change('language:chars_replaced')
    def _chars_replaced_on_load(self):
        self._notify_external_change('chars_replaced')
        self.code_widget.toggle_read_only()

    #### Trait initializers ###################################################

    def _language_default(self):
        # Sanity check.
        if not self.languages:
            return PythonHelper()

        # If the file has a path, try to choose the helper from its extension.
        elif self.obj.path:
            path_lower = self.obj.path.lower()
            for language in self.languages:
                for extension in language.extensions:
                    if path_lower.endswith(extension):
                        return language

        # We don't know what to do with the extension. If the file has no name,
        # go with Python since most new files will be Python scripts; otherwise,
        # choose Plain Text.
        name = 'Plain Text' if self.obj.path else 'Python'
        for language in self.languages:
            if language.name == name:
                return language

    def _name_default(self):
        # Get all untitled code_editors
        code_editors = [e for e in self.editor_area.editors \
                        if isinstance(e, CSVEditor) and len(e.obj.path) == 0
                        and e is not self]
        num = max([int(e.name.split('-')[1]) for e in code_editors] + [0]) + 1
        return 'untitled-%d' % num

    def _obj_default(self):
        return File('')

    def __watcher_default(self):
        app = self.editor_area.task.window.application
        watcher = app.get_service(FileSystemWatcher)
        return watcher

    #### Trait change handlers ################################################

    def _obj_changed(self, old, new):
        # Nothing to do if code widget is not yet created.
        if self.code_widget is None:
            return

        # Needed to restore position from restored state.
        line, col = self.position

        # First manually clear out the text. This will prevent a potentially
        # expensive syntax highlighting call when the language is set.
        self.text = self._original_text = ''
        self.encoding = 'ascii'

        # Set the language plugin now to ensure that load() is appropriate for
        # the file extension.
        self.language = self._language_default()

        # The path will be the empty string if we are editing a file that has
        # not yet been saved.
        if len(new.path) == 0:
            self.name = self._name_default()
        else:
            self.name = basename(new.path)

            if exists(new.path):
                try:
                    self.load()
                except EnvironmentError, exc:
                    logger.exception(exc)
                    dialog = MessageDialog(severity='error',
                        title='Error',
                        message='Unable to open file "%s"' % new.path,
                        informative=exc.strerror,
                        detail=str(exc))
                    dialog.open()
                except Exception, exc:
                    logger.exception(exc)
                    dialog = MessageDialog(severity='error',
                        title='Error',
                        message='Error while opening file "%s"' % new.path,
                        detail=str(exc))
                    dialog.open()
            else:
                # Creating a file with path should make it dirty so that
                # user can save an empty new file (such as __init__.py)
                self.dirty = True

        self.position = [line, col]

        self._path_changed(old.path, new.path)

    @on_trait_change('closing')
    def window_closing(self, event):
        close = self._confirm_close()
        if not close:
            event.veto = True

    def _code_warnings_changed(self):
        if self.status_widget and self.is_active:
            self.status_widget.trait_set(warnings = len(self.code_warnings))

    @on_trait_change('status_widget:warnings_toggle')
    def warnings_toggled_in_status(self, value):
        if self.is_active and self.traits_inited():
            self.code_widget.toggle_warnings(value)

    @on_trait_change('position[]')
    def _update_cursor_position(self):
        if self.code_widget is None:
            return

        line, column = self.position
        if self.line != line:
            self.goto_line(line)
        if self.column != column:
            self.goto_column(column)

        if self.status_widget and self.is_active:
            self.status_widget.trait_set(line_number = self.line,
                                      column_number = self.column)

    def _is_active_changed(self, value):
        if self.control and value:
            self._update_cursor_position()
            self._code_warnings_changed()
            if self.status_widget:
                self.status_widget.current_language = self.language.name
                self.warnings_toggled_in_status(self.status_widget.warnings_toggle)

    #@on_trait_change('obj.path') # y u no work???
    # need to manually call it whereever path is changed
    def _path_changed(self, old, new):
        if old:
            self._watcher.remove_path(old)
        if new:
            self._watcher.add_path(new)
        save_action = self.get_action(SaveAction)
        save_action.enabled |= len(new) == 0

    @on_trait_change('status_widget:line_number')
    def line_number_changed_in_status(self, value):
        if self.is_active and self.line != value and self.traits_inited():
            self.goto_line(value)

    @on_trait_change('status_widget:column_number')
    def column_number_changed_in_status(self, value):
        if self.is_active and self.column != value and self.traits_inited():
            self.goto_column(value)

    @on_trait_change('status_widget:current_language')
    def language_changed_in_status(self, value):
        if self.is_active:
            for language in self.languages:
                if language.name == value:
                    self.language = language
                    break

    @on_trait_change('language')
    def update_language_in_status(self, value):
        if self.status_widget and self.is_active:
            self.status_widget.current_language = value.name

    @on_trait_change('costly_position_changed_event')
    def highlight_occurrences(self):
        if not (self.highlight_occurrences_enabled and self.editor_area):
            return False

        # Do not highlight occurrences if code_widget cursor has selection.
        if self.code_widget.textCursor().hasSelection():
            return False

        service = self.code_helper
        if service is None:
            return False

        root, fname = self._get_project_path()
        source = self.text
        pos = self.cursor.position()

        occurrences = service.get_occurrences_local(root, source, pos, fname)[1]
        self.code_widget.highlight_occurrences(occurrences)

    def _highlight_occurrences_enabled_changed(self, value):
        if value:
            # Highlight occurrences without waiting for cursor position change.
            self.highlight_occurrences()
        else:
            # Clear all highlighted occurrences.
            self.code_widget.highlight_occurrences([])

    def _smart_parenthesis_enabled_changed(self, value):
        if self.code_widget:
            self.code_widget.smart_paren_closing = value

    def _update_tooltip_promise(self, promise):
        """ Update current tooltip with result from promise.
        """
        for i, (s,k,v) in enumerate(self._tooltip_parts):
            if v == promise:
                self._tooltip_parts[i] = s, k, str(promise.result)
                break
        else:
            # tooltip hidden already
            pass
        self._show_current_tooltip_text(pos=self._last_tooltip_pos, update=False)

    def _show_current_tooltip_text(self, pos, update=False):
        """ Show/update the current tooltip.
        """
        tooltips = self._tooltip_parts
        if len(tooltips) > 0:
            tooltip = []
            has_something = False
            symbols = set(s for s,_,_ in tooltips)
            show_symbols = len(symbols) > 1
            prev_symbol = None
            for symbol, kind, value in sorted(tooltips):
                if isinstance(value, Promise):
                    value.dispatch = 'ui'
                    value.on_done(lambda result, promise=value:
                                        self._update_tooltip_promise(promise))
                    value = 'loading...'
                else:
                    has_something = True
                if show_symbols and symbol != prev_symbol:
                    tooltip.append('%s:\n%s'%(symbol, value))
                else:
                    tooltip.append(value)

            tooltip = '\n\n'.join(tooltip)

            if not has_something:
                # Not a single tooltip data available, nothing to show.
                return False

            if update:
                return self.code_widget.update_tip(self._last_tooltip_id, tooltip)
            else:
                self._last_tooltip_id = self.code_widget.show_tip(tooltip, pos)
                return True
        return False

    #### Traits property getters and setters ##################################

    @cached_property
    def _get_code_helper(self):
        if self.editor_area:
            app = self.editor_area.task.window.application
            service = app.get_service(CodeHelperService)
            return service.get_code_helper(self.language.name)
        else:
            return None

    @on_trait_change('costly_text_changed_event,code_helper')
    def _get_code_warnings(self):
        if not self.editor_area or not self.cursor:
            return False

        service = self.code_helper
        if service is None:
            warnings = []
        else:
            # Try and determine the filename and root directory.
            if len(self.obj.path) == 0:
                root = ''
                fname = ''
            else:
                pth = self.obj.absolute_path
                root = dirname(pth)
                fname = basename(pth)
            pos = self.cursor.line()+1

            warnings = service.get_warnings(root, self.text, pos, fname)

        self.code_warnings = warnings
        if self.code_widget:
            self.code_widget.set_warnings(warnings)

    def _get_tooltip(self):
        return self.obj.path or self.name

    def _get__text_hash(self):
        from hashlib import md5
        text = self.text.replace('\n', self._linesep).encode(self.encoding)
        return md5(text).digest()

    @on_trait_change('obj.path')
    def _update_reload_action(self, value):
        from canopy.editor.common_editor_actions import ReloadAction
        if value is not None and len(value) > 0:
            self.get_action(ReloadAction).enabled = True

    @on_trait_change('loaded,language')
    def _update_run_file_action(self):
        language = self.language
        from canopy.code_editor.code_editor_actions import RunFileAction
        run_file_action = self.get_action(RunFileAction)

        if isinstance(language, PythonHelper) and language.name != 'Enaml':
            run_file_action.enabled = run_file_action.visible = True
        else:
            run_file_action.visible = True
            run_file_action.enabled = False


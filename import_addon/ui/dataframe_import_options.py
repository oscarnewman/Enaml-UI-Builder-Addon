import re
import os
import traceback

import enaml
import traits_enaml
from enaml.qt.qt_application import QtApplication
from traits.api import (
    HasTraits, Str, HTML, List, Int, Bool, Dict, Any, Instance, Either
)
import pandas as pd
from enaml_ui_builder import application
from enaml_ui_builder.app.data_frame_plugin import DataFramePlugin
import numpy as np
from canopy.file_handling.i_file_handling_service import IFileHandlingService

from import_addon.transfer_handler import TransferHandler

class DataFrameImportOptions(HasTraits):
    """Class to handle options for importing CSV and model for enaml view.
    """

    # Index of header row
    header_row = Any(0)

    # Indexes of columns to use as index columns
    index_column = Str('None')

    # Indexes entered as comma separated list
    index_sequence = Str()

    # Html to be used in preview of dataframe
    html = HTML()

    # Whether to parse dates
    parse_dates = Bool(False)

    # Path to CSV file
    path = Str()

    # DataFrame for CSV file
    df = Instance(pd.DataFrame)

    # DF after transfers applied
    df_trans = Instance(pd.DataFrame)

    # CSS for dataframe html
    style = Str("<style type='text/css'>html, body{margin: 0;padding:\
                0;width:100%;}table{width:100%;height:100%;\
                border-collapse:collapse;font-family: monospace;margin:\
                0;border-collapse:collapse;\
                }td{padding: 0 10px;background: #ffffff;}th{text-align:\
                center;padding: 5px;background: #f7f7f7;}</style>")

    # Application instance used to acces python frontend
    application = Instance('envisage.api.IApplication') 

    transfer_handler = Instance(TransferHandler)

    # Currently selected dataframe column
    selected_column = Any()

    # Error output by transfer
    last_error = Any(None)

    # Plain text of file
    plain_text = Str()

    # whether the parser failed
    parse_error = Bool(False)

    ## Defaults

    def _df_default(self):
        return pd.DataFrame()

    def _df_trans_default(self):
        return self.df.copy()

    def _transfer_handler_default(self):
        return TransferHandler(self.df)

    # Monitor for changes

    def _path_changed(self):
        self._update_dataframe()

    def _header_row_changed(self):
        self._update_dataframe()

    def _index_column_changed(self):
        self._update_dataframe()

    def _index_sequence_changed(self):
        self._update_dataframe()
        
    def _parse_dates_changed(self):
        self._update_dataframe()

    def _selected_column_changed(self):
        self._update_dataframe()

    ## Logic for Dataframes and preview

    def _update_dataframe(self):
        try:
            self._read_dataframe()
            self._update_html()
            self.parse_error = False
        except: 
            self.parse_error = True

        self.plain_text = open(self.path, 'r').read()
        self.transfer_handler.update_dataframe(self.df)
        self.df_trans = self.transfer_handler.apply_transfers()
        if self.selected_column in list(self.df.columns.values):
            self.last_error = self.transfer_handler.errors[self.selected_column]
        

    def _read_dataframe(self):
        raise NotImplementedError()

    def _update_html(self):
        self.html = (self.style + self.df_trans.to_html(max_rows=5)).encode('ascii', 'xmlcharrefreplace')

    def _update_html_parse_error(self, error=""):
        error = "<style type='text/css'>*{background:#ffffff;color:red;\
                font-family:monospace;}p{width: 250px; margin: 0 auto;\
                text-align: center;}\
                </style><p>Data could not be parsed.</p><p>"+error+"</p>"
        self.html = error

    def _get_current_index_col(self):
        """Returns index_column converted from string into appropriate datatype
        """
        if self.index_column == 'Multi-Index':
            sequence_array = filter(None, re.compile(r'\d*').findall(self.index_sequence))
            if(len(sequence_array) == 0):
                return None
            else:
                return map(int, sequence_array)
        elif self.index_column == 'None':
            return None
        else:
            return int(self.index_column)

    def open_transfers_file(self):
        """ Opens the transfer functions file in canopy.
        """
        file = open(self.transfer_handler.user_transfers_path, 'a+')
        service = self.application.get_service(IFileHandlingService)
        service.open_file(self.transfer_handler.user_transfers_path)

    def reload_transfers(self):
        """ Prompts transfer handler to reload tranfer functions and updates
            table
        """
        self.transfer_handler.reload_transfers()
        self._update_dataframe()

    def _generate_code(self):
        return "print 'Code generation not properly implemented.'"

    ## Method called when OK is pressed
    def ok_pressed(self):

        code = self._generate_code()
        code_task = self.application.get_task('canopy.integrated_code_editor')

        # Make the python pane visible, if it is not
        if not code_task.python_pane.visible:
            code_task.python_pane.visible = True

        # Run the code in the frontend
        code_task.python_pane.frontend.execute_command(code)
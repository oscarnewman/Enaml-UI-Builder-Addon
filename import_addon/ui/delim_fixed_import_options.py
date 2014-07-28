import re

import enaml
import traits_enaml
from enaml.qt.qt_application import QtApplication
from traits.api import (
    HasTraits, Str, HTML, List, Int, Bool, Dict, Any, on_trait_change
)
import pandas as pd

from dataframe_import_options import DataFrameImportOptions

class DelimFixedImportOptions(DataFrameImportOptions):
    """Class to handle options for importing CSV and model for enaml view.
    """
    
    # What type of file is being read
    ftype = Str('delimited')

    ### Delimited

    # Keys for delimiters - separated to maintain original order
    delims_keys = ['comma', 'space', 'tab', 'semicolon', '--','custom']

    # Values for Delimiters
    delims_vals = [',', ' ', '\t', ';', '--','']

    # Compiled Dictionary
    delims_dict = dict(zip(delims_keys, delims_vals))

    # Delimiter selected by user
    delim = Str(',')

    ### Fixed Width

    # Keys for delimiters - separated to maintain original order
    col_width_sequence = Str()

    # ## Detect Changes in Traits

    def _delim_changed(self):
        self._update_dataframe()

    def _ftype_changed(self):
        self._update_dataframe()

    def _col_width_sequence_changed(self):
        self._update_dataframe()

    # ## Logic for Dataframes and preview

    def _read_delimited(self):
        self.df = pd.read_csv(self.path, 
                             sep=self.delim,
                             header=self.header_row,
                             parse_dates=self.parse_dates,
                             index_col=self._get_current_index_col(),
                             encoding='utf-8')

    def _read_fixed(self):
        self.df = pd.read_fwf(
            self.path, 
            widths=self._get_widths(),
            parse_dates=self.parse_dates,
            header=self.header_row,
            index_col=self._get_current_index_col(),
            encoding='utf-8'
        )

    def _read_dataframe(self):
        if self.ftype == 'delimited':
            self._read_delimited()
        elif self.ftype == 'fixed':
            self._read_fixed()

    def _get_widths(self):
        sequence_array = filter(None, re.compile(r'\d*').findall(self.col_width_sequence))
        if(len(sequence_array) == 0):
            return None
        else:
            return map(int, sequence_array)

    def _generate_code(self):
        imports = """
import pandas as pd
from enaml_ui_builder import application
from enaml_ui_builder.app.data_frame_plugin import DataFramePlugin
"""
        create_df = "df = pd.read_csv('{}',sep='{}',header={},parse_dates={},index_col={},encoding='utf-8')".format(
            str(self.path), str(self.delim), str(self.header_row), str(self.parse_dates), 
            ("'"+str(self._get_current_index_col())+"'") if self._get_current_index_col() is not None else 'None'
            )

        to_print = "\n\nprint 'dataframe created in variable `df`'"
        return imports + create_df + to_print

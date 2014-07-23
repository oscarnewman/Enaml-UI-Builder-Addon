import re

import enaml
import traits_enaml
from enaml.qt.qt_application import QtApplication
from traits.api import (
    HasTraits, Str, HTML, List, Int, Bool, Dict, Any, on_trait_change
)
import pandas as pd
from enaml_ui_builder import application
from enaml_ui_builder.app.data_frame_plugin import DataFramePlugin

from dataframe_import_options import DataFrameImportOptions

class CSVImportOptions(DataFrameImportOptions):
    """Class to handle options for importing CSV and model for enaml view.
    """

    # Keys for delimiters - separated to maintain original order
    delims_keys = ['comma', 'space', 'tab', 'semicolon', 'custom']

    # Values for Delimiters
    delims_vals = [',', ' ', '\t', ';', '']

    # Compiled Dictionary
    delims_dict = dict(zip(delims_keys, delims_vals))

    # Delimiter selected by user
    delim = Str(',')

    # ## Detect Changes in Traits

    def _delim_changed(self):
        self._update_dataframe()

    # ## Logic for Dataframes and preview

    def _update_dataframe(self):
        # try:
        self.df = pd.read_csv(self.path, 
                             sep=self.delim,
                             header=self.header_row,
                             parse_dates=self.parse_dates,
                             index_col=self._get_current_index_col(),
                             encoding='utf-8')
        super(CSVImportOptions, self)._update_dataframe()
        self._update_html()
        # except:
        #     self._update_html_parse_error()

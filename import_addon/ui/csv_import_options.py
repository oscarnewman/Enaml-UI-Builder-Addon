import re

import enaml
import traits_enaml
from enaml.qt.qt_application import QtApplication
from traits.api import (
    HasTraits, Str, HTML, List, Int, Bool, Dict, Any, on_trait_change
)
import pandas as pd

from dataframe_import_options import DataFrameImportOptions

class CSVImportOptions(DataFrameImportOptions):
    """Class to handle options for importing CSV and model for enaml view.
    """

    # Keys for delimiters - separated to maintain original order
    delims_keys = ['comma', 'space', 'tab', 'semicolon', '--','custom']

    # Values for Delimiters
    delims_vals = [',', ' ', '\t', ';', '--','']

    # Compiled Dictionary
    delims_dict = dict(zip(delims_keys, delims_vals))

    # Delimiter selected by user
    delim = Str(',')

    # ## Detect Changes in Traits

    def _delim_changed(self):
        self._update_dataframe()

    # ## Logic for Dataframes and preview

    def _read_dataframe(self):
        self.df = pd.read_csv(self.path, 
                             sep=self.delim,
                             header=self.header_row,
                             parse_dates=self.parse_dates,
                             index_col=self._get_current_index_col(),
                             encoding='utf-8')

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
        view_func = """
def view_dataframe(dataframe):
    print 'Launching Enaml UI Builder...'
    app = application()
    app.add_plugin(DataFramePlugin(data_frame=dataframe))
    app.start()
"""
        to_print = "\n\nprint 'dataframe created in variable `df`'\nprint 'View in UI Builder with `view_dataframe(df)`'"
        return imports + create_df + view_func + to_print

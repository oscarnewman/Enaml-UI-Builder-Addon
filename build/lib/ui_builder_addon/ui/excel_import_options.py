from traits.api import Str

import pandas as pd
from enaml_ui_builder import application
from enaml_ui_builder.app.data_frame_plugin import DataFramePlugin

form dataframe_import_options import DataFrameImportOptions

class ExcelImportOptions(DataFrameImportOptions):
    """Class to handle options for importing CSV and model for enaml view.
    """

    sheet = Str()

    def _sheet_changed(self):
        self._update_dataframe()

    def _update_dataframe(self):
        try:
            xls = pd.ExcelFile(self.path)
            self.df = xls.parse(
                self.sheet,
                header=self.header_row,
                parse_dates=self.parse_dates,
                index_col=self._get_current_index_col(),
                encoding='utf-8'
            )
            self._update_html()
        except:
            self._update_html_parse_error()
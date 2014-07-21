import sys

from traits.api import Str, Instance, List
import pandas as pd
from enaml_ui_builder import application
from enaml_ui_builder.app.data_frame_plugin import DataFramePlugin

from dataframe_import_options import DataFrameImportOptions

class ExcelImportOptions(DataFrameImportOptions):
    """Class to handle options for importing Excel files
    """

    sheet = Str()

    sheets = List([])

    def _path_changed(self):
        self._update_datafame()

    def _sheet_changed(self):
        self._update_dataframe()

    def _update_dataframe(self):
        self.xls = pd.ExcelFile(self.path)
        self.sheets = self.xls.sheet_names
        self.df = self.xls.parse(
            # self.sheets[0],
            header=self.header_row,
            parse_dates=self.parse_dates,
            index_col=self._get_current_index_col(),
            encoding='utf-8'
        )
        self._update_html()
        # except:
        #     # self._update_html_parse_error(sys.exc_info()[0])
        #     self.html = sys.exc_info()[0]
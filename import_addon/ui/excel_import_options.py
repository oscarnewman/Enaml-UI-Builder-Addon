from traits.api import Str, List, Instance
import pandas as pd

from dataframe_import_options import DataFrameImportOptions

class ExcelImportOptions(DataFrameImportOptions):
    """Class to handle options for importing Excel files
    """

    sheet = Str()

    sheets = List([])

    xls = Instance(pd.ExcelFile)

    def _sheet_changed(self):
        self._update_dataframe()

    # Logic for Dataframes and preview

    def _update_dataframe(self):
        wasNone = self.xls is None
        self.xls = pd.ExcelFile(self.path)
        self.sheets = self.xls.sheet_names
        if wasNone:
            self.sheet = self.sheets[0]
        try:
            self.df = self.xls.parse(
                self.sheet,
                header=self.header_row,
                parse_dates=self.parse_dates,
                index_col=self._get_current_index_col(),
                encoding='utf-8'
            )
            self._update_html()
        except:
            self._update_html_parse_error()
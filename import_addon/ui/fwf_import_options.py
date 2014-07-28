import re

from traits.api import Str
import pandas as pd
from pandas.io.parsers import FixedWidthReader

from dataframe_import_options import DataFrameImportOptions

class FWFImportOptions(DataFrameImportOptions):
    """Class to handle options for importing CSV and model for enaml view.
    """

    # Keys for delimiters - separated to maintain original order
    col_width_sequence = Str()

    # # Plain text of file for colum setup
    # plain_text = Str()

    # col_widths_list = []

    # plain_text_rows = []
   
    def _col_width_sequence_changed(self):
        self._update_dataframe()

    def _update_dataframe(self):

        try:
            self.df = pd.read_fwf(
                self.path, 
                widths=self._get_widths(),
                parse_dates=self.parse_dates,
                header=self.header_row,
                index_col=self._get_current_index_col(),
                encoding='utf-8'
            )
            self._update_html()
        except:
            self._update_html_parse_error()

        # file = open(self.path, 'r')
        # self.plain_text = '<pre style="font-size:16px">' + file.read() + '</pre>'
        # self.plain_text_rows = file.readlines()

        # self.col_widths_list = []
        # for i, col in self.df.iteritems():
        #     self.col_widths_list.append(col.map(str).map(len).max())
        # self.plain_text = str(self.col_widths_list)

    def _get_widths(self):
        sequence_array = filter(None, re.compile(r'\d*').findall(self.col_width_sequence))
        if(len(sequence_array) == 0):
            return None
        else:
            return map(int, sequence_array)

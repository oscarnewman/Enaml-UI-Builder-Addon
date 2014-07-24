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

from ui_builder_addon import default_transfers
from ui_builder_addon.transfer_handler import TransferHandler

class DataFrameImportOptions(HasTraits):
    """Class to handle options for importing CSV and model for enaml view.
    """

    # def __init__(self):
        # Execute Transfer Functions file if exists.
        # self._load_transfer_functions()


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
    df = pd.DataFrame()

    # DF after transfers applied
    df_trans = pd.DataFrame()

    # CSS for dataframe html
    style = Str("<style type='text/css'>html, body{margin: 0;padding:\
                0;width:100%;}table{width:100%;height:100%;\
                border-collapse:collapse;font-family: monospace;margin:\
                0;border-collapse:collapse;\
                }td{padding: 0 10px;background: #ffffff;}th{text-align:\
                center;padding: 5px;background: #f7f7f7;}</style>")

    # Application instance used to acces python frontend
    application = Instance('envisage.api.IApplication') 

    transfer_handler = TransferHandler(df)

    # Detect Changes in Traits
    transfer_functions = Dict()

    # path of transfer functions file
    transfer_functions_path = os.path.expanduser("~") + '/.canopy/transfers.py'

    # transfer function selected by the user
    selected_transfer_functions = Dict()

    # Currently selected dataframe column
    selected_column = Str()

    # Default datatypes to present to user
    default_dtypes = Dict({
        np.int64                        : 'Int',
        np.bool_                        : 'Bool',
        np.float64                      : 'Float',
        str                             : 'String',
        default_transfers.to_unicode    : 'Unicode'
    })

    # Error output by transfer
    last_error = Any(None)


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

    def _selected_transfer_functions_changed(self):
        self._update_dataframe()

    def _selected_column_changed(self):
        self._update_dataframe()

    ## Logic for Dataframes and preview

    def _update_dataframe(self):
        # self.df_trans = self.df.copy()
        # self._apply_transfers()
        self.transfer_handler.update_dataframe(self.df)
        self.df_trans = self.transfer_handler.apply_transfers()
        if self.selected_column in list(self.df.columns.values):
            self.last_error = self.transfer_handler.errors[self.selected_column]

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


    # def _load_transfer_functions(self):
    #     """ Load transfer functions into dictionary from python file or create
    #         transfer function file if it doesn't already exist.
    #     """
    #     # Create file if it doesn't exist
    #     file = open(self.transfer_functions_path, 'a+')

    #     # Execute file and store local namespace to self.transfer_functions
    #     execfile(self.transfer_functions_path, {}, self.transfer_functions)

    # def _map_to_col(self, col, func):
    #     self.df_trans[col] = map(func, self.df[col])

    # def _apply_transfers(self):
    #     for col in self.selected_transfer_functions.keys():
    #         func = self.selected_transfer_functions[col]
    #         if func is not 'None' and func is not None:
    #             try:
    #                 if func not in self.default_dtypes.values():
    #                     self.df_trans[col] = map(self.transfer_functions[self.selected_transfer_functions[col]], self.df[col])
    #                 else:
    #                     # self.df_trans[col] = self.df[col].astype(self._type_for_string(func))
    #                     self.df_trans[col] = map(self._type_for_string(func), self.df[col])
    #                 self.last_error = ""
    #             except Exception, e:
    #                 self.last_error = str(np.random.randint(30)) + str(traceback.format_exc())


    # def _type_for_string(self, typestr):
    #     for key, val in self.default_dtypes.iteritems():
    #         if val == typestr:
    #             return key

    ## Method called when OK is pressed
    def ok_pressed(self):

        code = """
        import pandas as pd
        df =  pd.read_json('""" + self.df.to_json() + """')
        def _view(dataframe):
            import traits_enaml
            with traits_enaml.imports():
                from misc_views import DialogPopup
            print 'Launching Enaml UI Builder...'
            app = application()
            app.add_plugin(DataFramePlugin(data_frame=dataframe))
            app.start()

        """
        code_task = self.application.get_task('canopy.integrated_code_editor')

        # Make the python pane visible, if it is not
        if not code_task.python_pane.visible:
            code_task.python_pane.visible = True

        # Run the code in the frontend
        code_task.python_pane.frontend.execute_command(code)

        ## Launch UI Builder

        # with traits_enaml.imports():
        #     from misc_views import DialogPopup

        # dialog = DialogPopup()

        # dialog.show()

        # app = application()
        # app.add_plugin(DataFramePlugin(data_frame=self.df_trans))
        # app.start()

        # dialog.close()

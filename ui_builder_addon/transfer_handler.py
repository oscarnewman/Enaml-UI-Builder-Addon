import os
import logging
import sys
import traceback

import pandas as pd
import numpy as np

class TransferHandler():

    # Build in transfer functions and data types
    default_transfer_functions = {}

    # Transfer functions defined by the user
    user_transfer_functions = {}

    # Datatypes for each column as determined by Pandas
    default_column_dtypes = {}

    # Transfer functions for each column
    column_transfers = {}

    # Dataframe before transfers
    dataframe_original = pd.DataFrame()

    # Dataframe to apply transfers to
    dataframe_transferred = pd.DataFrame()

    # path of transfer functions file
    user_transfers_path = os.path.expanduser("~") + '/.canopy/transfers.py'

    # Aliases from normal data types names (Int, String, etc.) to Pandas
    # datatype names (integer, string, etc.)
    name_aliases = {}

    # Errors for each column
    errors = {}

    def __init__(self, df):
        self.dataframe_original = df
        self._load_column_dtypes()
        self._load_transfers()

    def _load_transfers(self):
        """ Load transfer functions into dictionary from python file or create
            transfer function file if it doesn't already exist.
        """
        # Create file if it doesn't exist
        file = open(self.user_transfers_path, 'a+')

        # Execute file and store local namespace to self.transfer_functions
        execfile(self.user_transfers_path, {}, self.user_transfer_functions)

        self.default_transfer_functions = {
            'Int' : int,
            'Float' : float,
            'String' : str,
            'Unicode (from utf-8)' : \
                lambda x: unicode(str(x), 'utf-8') if not isinstance(x, unicode) else x,
            'Boolean' : np.bool_
        }

        self.name_aliases = {
            'Int' : 'integer',
            'Float' : 'floating',
            'String': 'string',
            'Unicode (from utf-8)' : 'unicode',
            'Boolean' : 'boolean'
        }

    def _load_column_dtypes(self):

        # Column names of dataframe columns
        column_names = list(self.dataframe_original.columns.values)

        # Errors dict with column names as keys
        self.errors = dict((col, None) for col in column_names)

        # Datatype names as inferred by pandas
        inferred_dtypes = \
            list(self.dataframe_original.apply(
                # return inferred dtype name for each column
                lambda x: pd.lib.infer_dtype(x.values))
            )

        self.default_column_dtypes = dict(zip(column_names, inferred_dtypes))

        for col, type_name in self.default_column_dtypes.iteritems():
            if not col in self.column_transfers:
                self.column_transfers[col] = type_name

        poplist = []
        for col, type_name in self.column_transfers.iteritems():
            if not col in self.default_column_dtypes:
                poplist.append(col)

        for col in poplist:
            self.column_transfers.pop(col)

        # logging.info("COLUMN_TRANSFERS" + str(self.column_transfers))

    def apply_transfers(self):

        # Copy orginal dataframe to dataframe to be transferred
        self.dataframe_transferred = self.dataframe_original.copy()

        for col, transfer_name in self.column_transfers.iteritems():
            # logging.info('COL: ' + col + ' TRANSFER: ' + transfer_name)
            # Test if transfer is a default transfer
            if transfer_name in self.default_transfer_functions.keys():
                # Do nothing if the selected transfer is the default dtype
                if not self._is_default_dtype_for_column(transfer_name, col):
                    # Map the selected function to the column
                    func = self.default_transfer_functions[transfer_name]
                    self._map_to_col(func, col)

            # The transfer is a user defined function
            elif transfer_name in self.user_transfer_functions.keys():
                # Map the selected function to the column
                func = self.user_transfer_functions[transfer_name]
                self._map_to_col(func, col)

        return self.dataframe_transferred
               
    def _map_to_col(self, func, col):
        """ Maps a function to a column in dataframe_transferred.
        """
        try:
            self.dataframe_transferred[col] = \
                self.dataframe_transferred[col].apply(func)
            self.errors[col] = None
        except Exception as e:
            logging.error(e)
            self.errors[col] = 'Error: ' + str(np.random.randint(100)) + ' ' + str(e).encode('latin1')
            #self.errors[col] = traceback.format_exc()
            # self.errors[col] = str(np.random.randint(30)) + ": Sorry, this function could not be applied."
            # self.errors[col] = str(sys.exc_info()[1])
        # except Exception, e:
        #     self.errors[col] = str(e)

    def _is_default_dtype_for_column(self, type_name, column):
        name = type_name

        # Set name to actual value that pandas sees if it isn't already
        if type_name in self.name_aliases.keys():
            name = self.name_aliases[name]

        return self.default_column_dtypes[column] == name

    def get_list_options_for_column(self, column):
        options = []
        if not self.default_column_dtypes[column] in self.name_aliases.values():
            if not self.default_column_dtypes[column] in self.default_transfer_functions.keys():
                options.append(str(self.default_column_dtypes[column]))

        options += self.default_transfer_functions.keys()
        options += self.user_transfer_functions.keys()

        return options 

    def transfer_for_col(self, col):
        transfer = self.column_transfers[col]

        # Set transfer to actual value that pandas sees if it isn't already
        if transfer in self.name_aliases.values():
            transfer = self._key_for_val(self.name_aliases, transfer)
            # transfer = self.name_aliases[transfer]

        return transfer

    def set_col_transfer(self, col, transfer):
        self.column_transfers[col] = transfer

    def update_dataframe(self, df):
        self.dataframe_original = df
        self._load_column_dtypes()

    def _key_for_val(self, dict, val):
        for key, v in dict.iteritems():
            if v == val:
                return key
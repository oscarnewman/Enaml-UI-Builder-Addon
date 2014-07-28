import os
import logging
import sys
import math

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

    # Columns to ignore
    ignore_columns = {}

    # Aliases from normal data types names (Int, String, etc.) to Pandas
    # datatype names (integer, string, etc.)
    name_aliases = {}

    # Errors for each column
    errors = {}

    def __init__(self, df, path):
        self.dataframe_original = df
        self._load_column_dtypes()
        self._load_transfers()
        self.user_transfers_path = path + '/transfers.py'

    def _load_transfers(self):
        """ Load transfer functions into dictionary from python file or create
            transfer function file if it doesn't already exist.
        """
        # Create file if it doesn't exist
        file = open(self.user_transfers_path, 'a+')

        # Execute file and store local namespace to self.transfer_functions
        execfile(self.user_transfers_path, {}, self.user_transfer_functions)

        self.default_transfer_functions = {
            'Int' : \
                lambda x: None if isinstance(x, float) and math.isnan(x) else int(x),
            'Float' : float,
            'String' : str,
            'Unicode (from utf-8)' : self._convert_to_unicode,
            'Boolean' : np.bool_
        }

        self.name_aliases = {
            'Int' : 'integer',
            'Float' : 'floating',
            'String': 'string',
            'Unicode (from utf-8)' : 'unicode',
            'Boolean' : 'boolean'
        }

    def reload_transfers(self):
        """ Reload transfer functions into dictionary from python file or 
            create transfer function file if it doesn't already exist.
        """
        # Create file if it doesn't exist
        file = open(self.user_transfers_path, 'a+')

        # Reset Dictionary to remove old functions
        self.user_transfer_functions = {}

        # Execute file and store local namespace to self.transfer_functions
        execfile(self.user_transfers_path, {}, self.user_transfer_functions)

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

        # Add any new columns
        for col, type_name in self.default_column_dtypes.iteritems():
            if not col in self.column_transfers:
                self.column_transfers[col] = type_name
            if not col in self.ignore_columns:
                self.ignore_columns[col] = False


        # Remove old columns
        poplist = []
        for col, type_name in self.column_transfers.iteritems():
            if not col in self.default_column_dtypes:
                poplist.append(col)

        for col in poplist:
            self.column_transfers.pop(col)

    def apply_transfers(self):

        # Copy orginal dataframe to dataframe to be transferred
        self.dataframe_transferred = self.dataframe_original.copy()

        for col, transfer_name in self.column_transfers.iteritems():
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

        for col, drop in self.ignore_columns.iteritems():
            # Test if column should be dropped
            if drop:
                self.dataframe_transferred.drop(col, axis=1, inplace=True)

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
            if func is float:
                # Float error cannot be seen due to encoding issues.
                # Display generic error message. Will still fail on 
                # custom transfers.
                msg = "Conversion to float failed."
            else:
                msg = str(e)
            self.errors[col] = msg

    def _is_default_dtype_for_column(self, type_name, column):
        name = type_name

        # Set name to actual value that pandas sees if it isn't already
        if type_name in self.name_aliases.keys():
            name = self.name_aliases[name]

        return self.default_column_dtypes[column] == name

    def get_list_options_for_column(self, column):
        if column is None:
            return []

        options = []
        if not self.default_column_dtypes[column] in self.name_aliases.values():
            if not self.default_column_dtypes[column] \
                in self.default_transfer_functions.keys():
                options.append(str(self.default_column_dtypes[column]))

        options += self.default_transfer_functions.keys()
        options += self.user_transfer_functions.keys()

        return options 

    def transfer_for_col(self, col):

        if col is None:
            return None

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
    
    def set_ignore_column(self, column, ignore):
        self.ignore_columns[column] = ignore

    def is_column_ignored(self, column):
        return self.ignore_columns[column]

    def _key_for_val(self, dict, val):
        for key, v in dict.iteritems():
            if v == val:
                return key

    def _convert_to_unicode(self, value):
        if isinstance(value, str):
            try:
                return unicode(value, encoding='utf-8')
            except UnicodeDecodeError:
                return unicode(value, encoding='latin-1')
        else:
            return unicode(value)
#!/usr/bin/python
# -*- coding: utf-8 -*-
from traits.api import HasTraits, Enum, HTML, Int, List, Any, Range, \
    Bool
from traitsui.api import View, HGroup, Item, VGroup, Group, EnumEditor, \
    Handler, CSVListEditor
import pandas as pd


class CSVOptionsHandler(Handler):

    index_cols = List()

    def object_state_changed(self, info):

        self.index_cols = [None] + range(info.object.df.shape[1]) \
            + ['Multi-Index']

        info.object.index_column = self.index_cols[0]


class CSVOptions(HasTraits):

    """ Options for importing CSV to Pandas DataFrame """

    delimiter = Enum('comma', 'tab', 'semicolon', 'space', cols=1)
    html = HTML()
    parse_dates = Bool(True)

    index_column = Any
    current_index = None
    index_sequence = List(Range(low=0, high='high', is_float=False))

    high = 0

    delimiters = {
        'comma': ',',
        'tab': '\t',
        'semicolon': ';',
        'space': ' ',
        }

    def _delimiter_changed(self):
        self.make_dataframe()

    def _index_sequence_changed(self):
        if len(self.index_sequence[::]) == 0:
            self.current_index = None
        else:
            self.current_index = self.index_sequence
        self.make_dataframe()

    def _index_column_changed(self):
        if self.index_column == 'Multi-Index':
            if len(self.index_sequence[::]) == 0:
                self.current_index = None
            else:
                self.current_index = self.index_sequence
        else:
            self.current_index = self.index_column
        self.make_dataframe()

    def _parse_dates_changed(self):
        self.make_dataframe()

    def create_html(self, html):
        css = \
            "<style type='text/css'>html, body{margin: 0;padding:\
                0;background: #EDEDED;}table{width:\
                100%;border-collapse:collapse;font-family: monospace;margin:\
                0;position:absolute;bottom: 0;\
                }td{padding: 0 10px;background: #ffffff;}th{text-align:\
                center;padding: 5px;background: #f7f7f7;}</style>"
        return css + html

    # -- Traits View Definitions ------------------------------------------------

    def update_html(self):
        base_html = self.df.to_html(max_rows=5)
        compiled_html = self.create_html(base_html)
        self.html = compiled_html.encode('ascii', 'xmlcharrefreplace')

    def set_html_parse_error(self):
        error = \
            "<style type='text/css'>*{background:#EDEDED;color:red;\
                font-family:monospace;}p{position:absolute;bottom:0;}\
                </style><p>Data could not be parsed.</p>"
        self.html = error

    def make_dataframe(self):
        try:
            self.df = pd.DataFrame.from_csv(self.path,
                    index_col=self.current_index,
                    sep=self.delimiters[self.delimiter],
                    parse_dates=self.parse_dates)
            self.update_html()
        except:
            self.set_html_parse_error()

    def trait_view(self, var):
        self.make_dataframe()
        base_html = self.df.to_html(max_rows=5)
        compiled_html = self.create_html(base_html)
        self.high = self.df.shape[1] - 1

        self.html = compiled_html.encode('ascii', 'xmlcharrefreplace')

        return View(
            Group(
                HGroup(
                    VGroup(
                        Item('delimiter', style="custom"),
                        Item('parse_dates')
                    ),
                    "_",
                    VGroup(
                        Item('index_column', editor = EnumEditor(name = 'handler.index_cols')),
                        Item('index_sequence', 
                            visible_when="index_column == 'Multi-Index'", 
                            label="Index Columns (Comma Separated)", 
                            editor=CSVListEditor())
                    ),                    
                ),
                VGroup(
                    Item('html', label="Preview", show_label=False),
                ),
            layout="normal",
            ),
            title   = 'Load CSV to Enaml UI Builder',
            buttons = ['OK', 'Cancel' ],
            resizable = True,
            handler=CSVOptionsHandler
        )
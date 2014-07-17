				"""
				constraints = [
					hbox(
						vbox(
							delims_lbl,
							delims,
							delim_other,
							spacer
						), 
						spacer(50),
						vbox(
							header_row_lbl,
							has_header_row_cb,
							header_row,
							spacer
						), 
						spacer(50),
						vbox(
							index_cols_lbl,
							index_cols,
							multi_index_cols,
							spacer
						)
					),
					delims_lbl.width == delims.width,
					header_row_lbl.width == header_row.width,
					has_header_row_cb.width == header_row.width,
					index_cols_lbl.width == index_cols.width
				]
				"""
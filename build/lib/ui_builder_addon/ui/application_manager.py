"""
A basic module to ensure that only one QtApplication ever exists, allowing for
the UI Builder to be launched multiple times.

"""

from enaml.qt.qt_application import QtApplication

# The QTApplication Instance to be used by the CSV Importer
app = None

def app_exits():
	""" Whether a QtApplication has been created.

	"""
	return app is not None

def create_app():
	""" Creates an app only if one doesn't already exist.

	"""
	global app
	if not app_exits():
		app = QtApplication()
		app.start()

def stop_app():
	""" Stops the current app.

	"""
	app.stop()
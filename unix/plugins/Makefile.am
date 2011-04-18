
include $(top_srcdir)/Common.am

my_files = __init__.py jsonparser.py xscomm.py

dist_noinst_SCRIPTS = ${my_files}

dist_plugins_SCRIPTS = ${my_files:.py=.pyc}

${my_files:.py=.pyc}:
	${PYTHON_VER} -m py_compile ${@:.pyc=.py}

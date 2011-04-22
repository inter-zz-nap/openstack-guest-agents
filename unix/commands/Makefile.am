
include $(top_srcdir)/Common.am


my_files = __init__.py command_list.py network.py \
           update.py file_inject.py misc.py password.py

my_subdir_files = debian/__init__.py debian/network.py \
                  redhat/__init__.py redhat/network.py \
                  arch/__init__.py arch/network.py \
                  suse/__init__.py suse/network.py \
                  gentoo/__init__.py gentoo/network.py

dist_noinst_SCRIPTS = ${my_files}
nobase_dist_noinst_SCRIPTS = ${my_subdir_files}

nodist_commands_SCRIPTS = ${my_files:.py=.pyc}
nobase_nodist_commands_SCRIPTS = ${my_subdir_files:.py=.pyc}

${my_files:.py=.pyc} ${my_subdir_files:.py=.pyc}: ${my_files} ${my_subdir_files}
	${PYTHON_VER} -m py_compile ${@:.pyc=.py}


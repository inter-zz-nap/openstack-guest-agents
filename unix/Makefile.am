
include $(top_srcdir)/Common.am

ACLOCAL_MFLAGS = -I m4

AM_CFLAGS += -DAGENT_VERSION=\"@PACKAGE_VERSION@\" -DPLUGINS_DIR=\"${pluginsdir}\" -DDATA_DIR=\"${datadir}\" -fvisibility=hidden

SUBDIRS = lib src plugins commands tests

EXTRA_DIST = install_libs.py install_modules.py nova-agent.py \
			 run_tests.py patch_binary.py scripts/agent-smith

data_DATA = nova-agent.py

nodist_noinst_DATA = agentlib.so scripts/installer.sh \
					scripts/nova-agent.init

agentlib.so:
	    ln -s lib/.libs/agentlib.so agentlib.so

BINTARDIR = @PACKAGE@-`uname -s`-`uname -m`-@PACKAGE_VERSION@
BINTARNAME = ${BINTARDIR}.tar.gz
FULLBINTARDIR = $(top_srcdir)/${BINTARDIR}

check-local:
	@${PYTHON_VER} run_tests.py

install-exec-local:
	rm -f ${DESTDIR}${datadir}/../nova-agent.py
	ln -s ${datadir}/nova-agent.py ${DESTDIR}${datadir}/../nova-agent.py
	@$(PYTHON_VER) $(top_srcdir)/install_modules.py ${DESTDIR}$(modulesdir)
	@$(PYTHON_VER) $(top_srcdir)/install_libs.py ${DESTDIR}$(sbindir)/nova-agent $(DESTDIR)${datadir} ${DESTDIR}/$(libdir)
	@$(PYTHON_VER) $(top_srcdir)/patch_binary.py ${DESTDIR}${sbindir}/nova-agent ${DESTDIR} $(libdir)
	@$(PYTHON_VER) $(top_srcdir)/patch_libs.py ${DESTDIR}${datadir} $(libdir)

distclean-local:
	rm -f $(top_srcdir)/{configure,configure.in}
	rm -f $(top_srcdir)/{aclocal.m4,compile,config.guess,config.sub}
	rm -f $(top_srcdir)/{depcomp,install-sh,ltmain.sh,missing}
	find $(top_srcdir) -name Makefile.in -exec rm -f {} \;
	find $(top_srcdir) -name configure.in -exec rm -f {} \;
	rm -rf $(top_srcdir)/m4
	rm -rf $(top_srcdir)/autom4te.cache

clean-local::
	rm -f agentlib.so
	find . -name '*.gcov' -delete -o -name '*.gcda' -delete -o -name '*.gcno' -delete
	find . -name '*.pyc' -exec rm -f {} \;
	rm -rf $(top_srcdir)/${BINTARDIR}

coverage:: check
	for d in $(SUBDIRS) ; do cd $$d ; for f in *.c ; do gcov $$f; done ; cd ..; done

bintar: all
	@rm -rf ${FULLBINTARDIR}; mkdir ${FULLBINTARDIR}
	@$(MAKE) install DESTDIR=$(CURDIR)/${BINTARDIR}
	@mkdir ${FULLBINTARDIR}/${datadir}/etc
	@chmod -R go-rwx ${FULLBINTARDIR}
	@cp $(top_srcdir)/scripts/agent-smith ${FULLBINTARDIR}/${prefix}/sbin/.
	@cp $(top_srcdir)/scripts/nova-agent* ${FULLBINTARDIR}/${datadir}/etc/.
	@cp $(top_srcdir)/scripts/installer.sh ${FULLBINTARDIR}/.
	@chmod 700 ${FULLBINTARDIR}/${prefix}/sbin/agent-smith
	@chmod 700 ${FULLBINTARDIR}/${datadir}/etc/*
	@chmod 700 ${FULLBINTARDIR}/installer.sh
# agent-smith requires that we don't have a subdir in the tar
# once agent-smith is dead, we can use this
#	@tar -czf $(top_srcdir)/${BINTARNAME} -C $(CURDIR) ${BINTARDIR}
	@tar -czf $(top_srcdir)/${BINTARNAME} -C $(CURDIR)/${BINTARDIR} .
	@rm -rf ${FULLBINTARDIR}
	@echo ""
	@echo "Created $(BINTARNAME)"
	@echo ""

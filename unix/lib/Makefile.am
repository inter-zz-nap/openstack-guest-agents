
include $(top_srcdir)/Common.am

AM_CFLAGS += -DAGENT_VERSION=\"@PACKAGE_VERSION@\" -fvisibility=hidden

noinst_HEADERS = libagent_int.h plugin_int.h logging_int.h \
                 agentlib.h plugin.h logging.h

lib_LTLIBRARIES = libagent.la
modules_LTLIBRARIES = agentlib.la

libagent_la_SOURCES = plugin.c logging.c

agentlib_la_SOURCES = agentlib.c
agentlib_la_LDFLAGS = -module -avoid-version
agentlib_la_LIBADD = libagent.la


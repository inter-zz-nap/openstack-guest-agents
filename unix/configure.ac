AC_PREREQ([2.59])
AC_INIT([nova-agent], [0.0.1.22], [chris.behrens@rackspace.com])
AC_CONFIG_SRCDIR([src/nova-agent.c])
AC_CONFIG_HEADERS([include/config.h])

AM_INIT_AUTOMAKE([foreign -Wall -Werror tar-ustar])

AC_PREFIX_DEFAULT([/usr])

AC_ARG_ENABLE([coverage],
  [AS_HELP_STRING([--enable-coverage],
    [Toggle coverage @<:@default=off@:>@])],
  [ac_coverage="$enableval"],
  [ac_coverage="no"])

AS_IF([test "$ac_coverage" = "yes"],
  [
    GCOV_CFLAGS="-fprofile-arcs -ftest-coverage -lgcov -O0"
  ])


AC_PROG_CC
AM_PROG_CC_C_O
AC_PROG_LIBTOOL
AC_CONFIG_MACRO_DIR([m4])

missing() {
    what="$1"
    echo ""
    echo "The $what is missing and is required for building"
    echo ""
}

if test "$PYTHON_CFLAGS" = "" -a "$PYTHON_LIB" = ""; then
    AC_MSG_CHECKING([for python build requisites])

    for python in "python2.7" "python2.6" "python2.5" "python2.4" ; do
        for dir in $prefix "/usr/local" "/usr"; do
            if test -f ${dir}/include/${python}/Python.h ; then
                if test -f ${dir}/lib/lib${python}.so ; then
                    # We're done.  Found header and library
                    PYTHON_VER=${python}
                    PYTHON_CFLAGS="-I${dir}/include/${python}"
                    PYTHON_LIB="-l${python}"
                    break
                fi
            fi
        done
    done

    if test "x${PYTHON_CFLAGS}" = "x" ; then
        AC_MSG_RESULT([not found])
    else
        AC_MSG_RESULT([adding ${PYTHON_CFLAGS} and ${PYTHON_LIB}])
    fi
fi

# Make sure to add this, so we don't need to manually add it on FreeBSD
LDFLAGS="$LDFLAGS -L/usr/local/lib"

AC_MSG_CHECKING([that the python library can be linked])

SAVE_CFLAGS=$CFLAGS
SAVE_LIBS=$LIBS

CFLAGS="$CFLAGS $PYTHON_CFLAGS"
LIBS="$LIBS $PYTHON_LIB"

AC_TRY_LINK([#include <Python.h>], [
int main(int argc, char **argv)
{
    Py_Main(argc, argv);
}
], [AC_MSG_RESULT([yes])], [

    AC_MSG_RESULT([no])
    AC_MSG_RESULT([])
    AC_MSG_RESULT([A working python header and/or library could not be found])
    AC_MSG_RESULT([Re-run configure specifying PYTHON_CFLAGS and PYTHON_LIB])
    AC_MSG_RESULT([and/or CFLAGS and LDFLAGS correctly])

    exit 1

    ])

LIBS=$SAVE_LIBS
CFLAGS=$SAVE_CFLAGS

AC_CHECK_PROG([PATCHELF], [patchelf], [yes])
if test "$PATCHELF" != "yes"; then
    missing "patchelf"
    exit 1
fi

# Check for certain headers
AC_CHECK_HEADERS(crypt.h)

AC_CHECK_LIB([crypt], [crypt])

AC_CHECK_LIB([pthread], [pthread_create], [], [
    missing "the pthread library"
    exit 1
])

DESTDIR="/"

AC_SUBST([GCOV_CFLAGS])
AC_SUBST([PYTHON_VER])
AC_SUBST([PYTHON_CFLAGS])
AC_SUBST([PYTHON_LIB])
AC_SUBST([DESTDIR])

AC_CONFIG_FILES([Makefile
                 src/Makefile
                 lib/Makefile
                 plugins/Makefile
                 commands/Makefile
                 tests/Makefile
                 scripts/installer.sh
                 scripts/nova-agent.init
                 scripts/nova-agent.freebsd.init
                 ])

AC_OUTPUT


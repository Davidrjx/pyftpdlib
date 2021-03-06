#!/usr/bin/env python

# Copyright (C) 2007 Giampaolo Rodola' <g.rodola@gmail.com>.
# Use of this source code is governed by MIT license that can be
# found in the LICENSE file.

import logging
import sys
import warnings
try:
    from StringIO import StringIO as BytesIO
except ImportError:
    from io import BytesIO

from pyftpdlib._compat import PY3
from pyftpdlib.servers import FTPServer
from pyftpdlib.test import mock
from pyftpdlib.test import safe_mkdir
from pyftpdlib.test import safe_rmdir
from pyftpdlib.test import TESTFN
from pyftpdlib.test import ThreadWorker
from pyftpdlib.test import unittest
from pyftpdlib.test import VERBOSITY
import pyftpdlib
import pyftpdlib.__main__


class TestThreadWorker(unittest.TestCase):

    def test_callback_methods(self):
        class Worker(ThreadWorker):

            def poll(self):
                if 'poll' not in flags:
                    flags.append('poll')

            def before_start(self):
                flags.append('before_start')

            def before_stop(self):
                flags.append('before_stop')

            def after_stop(self):
                flags.append('after_stop')

        # Stress test it a little to make sure there are no race conditions
        # between locks: the order is always supposed to be the same, no
        # matter what.
        for x in range(100):
            flags = []
            tw = Worker(0.001)
            tw.start()
            tw.stop()
            self.assertEqual(
                flags, ['before_start', 'poll', 'before_stop', 'after_stop'])


class TestCommandLineParser(unittest.TestCase):
    """Test command line parser."""
    SYSARGV = sys.argv
    STDERR = sys.stderr

    def setUp(self):
        class DummyFTPServer(FTPServer):
            """An overridden version of FTPServer class which forces
            serve_forever() to return immediately.
            """

            def serve_forever(self, *args, **kwargs):
                return

        if PY3:
            import io
            self.devnull = io.StringIO()
        else:
            self.devnull = BytesIO()
        sys.argv = self.SYSARGV[:]
        sys.stderr = self.STDERR
        self.original_ftpserver_class = FTPServer
        pyftpdlib.__main__.FTPServer = DummyFTPServer

    def tearDown(self):
        self.devnull.close()
        sys.argv = self.SYSARGV[:]
        sys.stderr = self.STDERR
        pyftpdlib.servers.FTPServer = self.original_ftpserver_class
        safe_rmdir(TESTFN)

    def test_a_option(self):
        sys.argv += ["-i", "localhost", "-p", "0"]
        pyftpdlib.__main__.main()
        sys.argv = self.SYSARGV[:]

        # no argument
        sys.argv += ["-a"]
        sys.stderr = self.devnull
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

    def test_p_option(self):
        sys.argv += ["-p", "0"]
        pyftpdlib.__main__.main()

        # no argument
        sys.argv = self.SYSARGV[:]
        sys.argv += ["-p"]
        sys.stderr = self.devnull
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

        # invalid argument
        sys.argv += ["-p foo"]
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

    def test_w_option(self):
        sys.argv += ["-w", "-p", "0"]
        with warnings.catch_warnings():
            warnings.filterwarnings("error")
            self.assertRaises(RuntimeWarning, pyftpdlib.__main__.main)

        # unexpected argument
        sys.argv = self.SYSARGV[:]
        sys.argv += ["-w foo"]
        sys.stderr = self.devnull
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

    def test_d_option(self):
        sys.argv += ["-d", TESTFN, "-p", "0"]
        safe_mkdir(TESTFN)
        pyftpdlib.__main__.main()

        # without argument
        sys.argv = self.SYSARGV[:]
        sys.argv += ["-d"]
        sys.stderr = self.devnull
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

        # no such directory
        sys.argv = self.SYSARGV[:]
        sys.argv += ["-d %s" % TESTFN]
        safe_rmdir(TESTFN)
        self.assertRaises(ValueError, pyftpdlib.__main__.main)

    def test_r_option(self):
        sys.argv += ["-r 60000-61000", "-p", "0"]
        pyftpdlib.__main__.main()

        # without arg
        sys.argv = self.SYSARGV[:]
        sys.argv += ["-r"]
        sys.stderr = self.devnull
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

        # wrong arg
        sys.argv = self.SYSARGV[:]
        sys.argv += ["-r yyy-zzz"]
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

    def test_v_option(self):
        sys.argv += ["-v"]
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

        # unexpected argument
        sys.argv = self.SYSARGV[:]
        sys.argv += ["-v foo"]
        sys.stderr = self.devnull
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)

    def test_D_option(self):
        with mock.patch('pyftpdlib.__main__.config_logging') as fun:
            sys.argv += ["-D", "-p 0"]
            pyftpdlib.__main__.main()
            fun.assert_called_once_with(level=logging.DEBUG)

        # unexpected argument
        sys.argv = self.SYSARGV[:]
        sys.argv += ["-V foo"]
        sys.stderr = self.devnull
        self.assertRaises(SystemExit, pyftpdlib.__main__.main)


if __name__ == '__main__':
    unittest.main(verbosity=VERBOSITY)

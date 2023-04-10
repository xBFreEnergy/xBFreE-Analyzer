# ##############################################################################
#                           GPLv3 LICENSE INFO                                 #
#  Copyright (c) 2023.  Mario S. Valdes-Tresanco and Mario E. Valdes-Tresanco  #
#                                                                              #
#  This program is free software; you can redistribute it and/or modify it     #
#  under the terms of the GNU General Public License version 3 as published    #
#  by the Free Software Foundation.                                            #
#                                                                              #
#  This program is distributed in the hope that it will be useful, but         #
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY  #
#  or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License    #
#  for more details.                                                           #
# ##############################################################################

import sys
import logging
from xBFreE.exceptions import xBFreEErrorLogging, CommandlineError
from xBFreEana.commandlineparser import anaparser
from xBFreEana.gui import GMX_MMPBSA_ANA
from utils import get_files

try:
    from PyQt6.QtWidgets import QApplication
    pyqt = True
except:
    try:
        from PyQt5.QtWidgets import QApplication
        pyqt = True
    except Exception:
        pyqt = False
finally:
    if not pyqt:
        xBFreEErrorLogging('Could not import PyQt5/PyQt6. xBFreE-Analyzer will be disabled until PyQt5/PyQt6 is '
                        'installed')


def run_xbfreeana():

    app = QApplication(sys.argv)
    app.setApplicationName('gmx_MMPBSA Analyzer (gmx_MMPBSA_ana)')
    try:
        parser = anaparser.parse_args(sys.argv[1:])
    except CommandlineError as e:
        xBFreEErrorLogging(f'{type(e).__name__}: {e}')
        sys.exit(1)
    ifiles = get_files(parser)
    w = GMX_MMPBSA_ANA(ifiles)
    w.show()
    sys.exit(app.exec())



if __name__ == '__main__':


    logging.info('Finished')

    # gmxmmpbsa()
    run_xbfreeana()
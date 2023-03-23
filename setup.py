# ##############################################################################
#                           GPLv3 LICENSE INFO                                 #
#                                                                              #
#  Copyright (C) 2020  Mario S. Valdes-Tresanco and Mario E. Valdes-Tresanco   #
#  Copyright (C) 2014  Jason Swails, Bill Miller III, and Dwight McGee         #
#                                                                              #
#   Project: https://github.com/Valdes-Tresanco-MS/gmx_MMPBSA                  #
#                                                                              #
#   This program is free software; you can redistribute it and/or modify it    #
#  under the terms of the GNU General Public License version 3 as published    #
#  by the Free Software Foundation.                                            #
#                                                                              #
#  This program is distributed in the hope that it will be useful, but         #
#  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY  #
#  or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License    #
#  for more details.                                                           #
# ##############################################################################

from setuptools import setup, find_packages
import versioneer

with open("README.md", "r") as f:
    LONG_DESCRIPTION = f.read()

setup(
    name='xBFreE-Analyzer',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    package_data={},
    license='BDS-3',
    author='Mario S. Valdes-Tresanco and Mario E. Valdes-Tresanco ',
    author_email='mariosergiovaldes145@gmail.com',
    maintainer='Mario S. Valdes-Tresanco',
    maintainer_email='mariosergiovaldes145@gmail.com',
    url='https://github.com/xBFreEnergy/xBFreE-Analyzer',
    description="xBFreE-Analyzer",
    long_description=LONG_DESCRIPTION,
    long_description_content_type='text/markdown',
    python_requires='>=3.8, <3.11',
    keywords=['xBFreE', 'xBFreEnergy', 'MMPBSA', 'MMGBSA', 'LIE', 'GROMACS', 'AMBER', 'NAMD', 'CHARMM', 'AmberTools'],
    install_requires=['pandas>=1.2.2', 'seaborn>=0.11.2', 'mpi4py>=3.1.3', 'scipy>=1.6.1', 'matplotlib>=3.5.1'],
    entry_points={
        "console_scripts": [
            "xbfree=xBFreE.app:run_xbfreex",
            ]}
)

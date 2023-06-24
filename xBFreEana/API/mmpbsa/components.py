import math
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd

from xBFreE.mmpbsa.utils.energy import emapping, flatten, get_std

# Enthalpy Example:
mmpbsasystem = {'normal': {'energy': {'gb': {'delta': {'VDW': None, 'EEL': None, 'TOTAL': None}}}}}
# Entropy Example:
mmpbsasystem2 = {'normal': {'ie': {'gb': {}}}}


class CalculationSystem:
    def __init__(self):
        pass

    def get_calculation_methods(self):
        """
        Return all the calculation methods. At the moment, only mmpbsa is implemented
        :return:
        """
        pass


class MMPBSACalculation:
    def __init__(self, sys_name, app_namespace, data):
        self.sys_name = sys_name
        self.app_namespace = app_namespace
        # self.subsystems = {'energy_normal': None, 'energy_mutant': None, 'energy_mutant-normal': None,
        #                    'decomp_normal': None, 'decomp_mutant': None,
        #                    # 'decomp_mutant-normal':None
        #                    }
        self.calculationtype = {'enthalpy': None, 'entropy': None, 'binding': None, 'decomposition': None}
        energy_keywords = ['energy_normal', 'energy_mutant', 'energy_mutant-normal']
        decomp_keywords = ['decomp_normal', 'decomp_mutant']#, 'decomp_mutant-normal']

        self.timestart = self.app_namespace.INPUT.get('timestart') or 0
        self.timestep = self.app_namespace.INPUT.get('timestep') or 0
        self.timeunit = self.app_namespace.INPUT.get('timeunit') or 'ps'


        # print(f"{self.app_namespace = }")
        self.frames_info = {
            'energy': {
                'startframe': self.app_namespace.INPUT['general']['startframe'],
                'interval': self.app_namespace.INPUT['general']['interval'],
                'numframes': self.app_namespace.INFO['numframes']},
            'time': {
                'timestart': self.timestart,
                'timestep': self.timestep,
                'timeunit': self.timeunit}
        }
        if self.app_namespace.INPUT['nmode']['nmoderun']:
            self.frames_info['nmode'] = {
                'startframe': self.app_namespace.INPUT['nmode']['nmstartframe'],
                'interval': self.app_namespace.INPUT['nmode']['nminterval'],
                'numframes': self.app_namespace.INFO['numframes_nmode']}

        # if data['energy_normal']:
        #     energy_data = {k.replace('energy_', ''): v for k, v in data.items() if k in energy_keywords and v}
        #     self.subsystems['energy'] = EnergySubSystem('energy', energy_data, frames_info)
        # if data['decomp_normal']:
        #     decomp_data = {k: v for k, v in data.items() if k in decomp_keywords}
        #     self.subsystems['energy_decomp'] = EnergySubSystem('energy_decomp', decomp_data, frames_info)

        enthalpy_data = {}
        entropy_data = {}
        bfe_data = {}

        for ek, ev in data.items():
            if ek in energy_keywords and ev:
                nek = ek.replace('energy_', '')
                enthalpy_data[nek] = {}
                entropy_data[nek] = {}
                bfe_data[nek] = {}

                for ss, ssv in ev.items():
                    enthalpy_data[nek][ss] = {}
                    entropy_data[ss] = {}
                    bfe_data[ss] = {}
                    for m, mv in ssv.items():
                        if m not in ['ie', 'c2', 'nmode', 'qh']:
                            enthalpy_data[nek][ss][m] = mv
                        else:
                            entropy_data[ss][m] = mv


        self.calculationtype['enthalpy'] = Enthalpy('enthalpy', enthalpy_data, index_info=self._get_frames_index())
        # self.calculationtype['enthalpy'] = Enthalpy('enthalpy', enthalpy_data, index_info=self._get_frames_index())
        # self.calculationtype['enthalpy'] = Enthalpy('enthalpy', enthalpy_data, index_info=self._get_frames_index())



    def setting_time(self, timestart=0, timestep=0, timeunit='ps'):
        """
        Define the time specifications. If the specifications were defined in the input file, then overwrite them
        :param timestart:
        :param timestep:
        :param timeunit:
        :return:
        """
        self.timestart = timestart
        self.timestep = timestep
        self.timeunit = timeunit

    def __getitem__(self, item):
        return self.calculationtype[item]

    def __repr__(self):
        return f'MMPBSACalculation(sys_name: {self.sys_name}'

    def get_calculation_types(self):
        """
        Return all the calculation types. For this
        :return:
        """
        pass

    def _get_frames(self):

        ts = self.frames_info['time']['timestep'] or 1

        numframes = self.frames_info['energy']['numframes']

        frames_list = list(
            range(
                self.frames_info['energy']['startframe'],
                self.frames_info['energy']['startframe'] + numframes * self.frames_info['energy']['interval'],
                self.frames_info['energy']['interval']
            ))
        # self.frames_list = frames_list
        self.frames_info['energy']['endframe'] = frames_list[-1]
        print(f"{self.frames_info['time'] = }")

        time_step_list = list(
            range(
                self.frames_info['time']['timestart'],
                self.frames_info['time']['timestart'] + len(frames_list) * ts * self.frames_info['energy']['interval'],
                ts * self.frames_info['energy']['interval']
            ))
        frames = dict(zip(frames_list, time_step_list))
        nmframes = None
        if self.frames_info.get('nmode'):
            nmnumframes = self.frames_info['nmode']['numframes']
            nmframes_list = list(
                range(
                    self.frames_info['nmode']['startframe'],
                    self.frames_info['nmode']['startframe'] + nmnumframes * self.frames_info['nmode']['interval'],
                    self.frames_info['nmode']['interval']
                ))
            print(f"{nmframes_list = }")
            if nmframes_list:
                self.frames_info['nmode']['endframe'] = nmframes_list[-1]

            nm_start = (nmframes_list[0] - frames_list[0]) * self.frames_info['energy']['interval']
            nmtime_step_list = list(
                range(
                    self.frames_info['time']['timestart'] + nm_start,
                    self.frames_info['time']['timestart'] + nm_start + len(nmframes_list) * ts * self.frames_info['nmode']['interval'],
                    ts * self.frames_info['nmode']['interval']
                ))
            # self.nmframes_list = nmframes_list
            nmframes = dict(zip(nmframes_list, nmtime_step_list))
        return frames, nmframes

    def _get_frames_index(self, framestype='energy', startframe=None, endframe=None, interval=1):
        frames, nmframes = self._get_frames()

        if framestype == 'energy':
            start = list(frames.keys()).index(startframe) if startframe else startframe
            end = list(frames.keys()).index(endframe) + 1 if endframe else endframe
            index_frames = {f: frames[f] for f in list(frames.keys())[start:end:interval]}
        else:
            if not nmframes:
                return
            start = list(nmframes.keys()).index(startframe) if startframe else startframe
            end = list(nmframes.keys()).index(endframe) + 1 if endframe else endframe
            index_frames = {f: nmframes[f] for f in list(nmframes.keys())[start:end:interval]}
        print(f"{index_frames = }")
        if self.frames_info['time']['timestep']:
            index = pd.Series(index_frames.values(), name=f"Time ({self.frames_info['time']['timeunit']})")
        else:
            index = pd.Series(index_frames.keys(), name='Frames')
        print(f"{index = }")
        return (start, end, index)

def model2df(energy, index, multiindex_names=None):
    energy_df = pd.DataFrame(flatten(energy), index=index)
    if multiindex_names:
        energy_df.columns.names = multiindex_names
    # print(energy_df.columns.names)
    s = pd.concat([energy_df.mean().round(3),
                   energy_df.std(ddof=0).round(3),
                   (energy_df.std(ddof=0) / math.sqrt(len(index))).round(3)],
                  axis=1)
    s.columns = ['Average', 'SD', 'SEM']
    summary_df = s.T
    df = pd.concat([energy_df, summary_df])
    df.index.name = index.name
    return df

class Enthalpy:
    def __init__(self, name, data, index_info):
        start, end, index = index_info


        self.data = model2df(data, index, ['subsystem', 'method', 'component', 'term'])
        print(self.data.head())
        df = self.data.iloc[
                            self.data.index.isin(['Average'])
                        ].unstack().reset_index().rename(columns={0: 'energy'})
        # print(df.head())
        df2 = self.data.iloc[
                            self.data.index.isin(['SD'])
                        ].unstack().reset_index().rename(columns={0: 'energy'})

        print('#############################')
        # df = self.data.iloc[
        #     self.data.index.isin(['Average', 'SD', 'SEM'])
        # ].unstack().reset_index().pivot(
        #     index=['subsystem', 'method', 'component', 'term'], columns='Frames'
        # ).droplevel(level=0, axis=1).reset_index().rename(columns={'Average': 'energy'})

        # print(self.data['normal', 'gb'])
        # print(self.data.loc[:, (['normal'], )])
        # print(self.data.xs(('normal', ('complex', 'delta')), level=(0, 2), axis=1))
    # def get_data(self, sele, level=0):
    #     if isinstance(sele, str):
        import seaborn as sns
        import matplotlib.pyplot as plt
        from xBFreEana.utils import bar_label

        g = sns.catplot(df, x='term', y='energy', hue='method', col='subsystem',
                        row='component', kind='bar',
                        sharey='row')
        # g.map(sns.barplot, "term", "energy", 'method')

        # methods = df['method'].unique()
        #
        # for axl, ax in g.axes_dict.items():
        #     axol = list(axl)
        #     axol.reverse()
        #     ax.bar_label(ax.containers[0], fmt='%.2f', color=sns.color_palette()[0])
        #     ax.bar_label(ax.containers[1], fmt='%.2f', color=sns.color_palette()[1])
        # # g.add_legend()
        #
        #     edf = df[(df['subsystem'] == axl[1]) & (df['component'] == axl[0])]
        #     print(edf['term'])
        #     vx = []
        #     vy = []
        #     yerr = []
        #     for m in methods:
        #         vx.append(edf[edf['method'] == m]['term'].to_list())
        #         vy.append(edf[edf['method'] == m]['energy'].to_list())
        #         yerr.append(edf[edf['method'] == m]['SD'].to_list())
        #
        #     vsx = []
        #     for e in zip(*vx):
        #         vsx.extend(e)
        #     vsy = []
        #     for e in zip(*vy):
        #         vsy.extend(e)
        #     syerr = []
        #     for e in zip(*yerr):
        #         syerr.extend(e)
        #
        #     print(f'{vsx = }')
        #     print(f'{vsy = }')
        #     print(f'{syerr = }')
        #     ax.errorbar(x=vsx, y=vsy,
        #                 yerr=syerr,
        #                 fmt='none',
        #                 errorevery=len(vx),
        #                 # zorder=1,
        #                 elinewidth=0.7,
        #                 capsize=5,
        #                 color='black')
        #     print(f"{ax.containers = }")
        #
        # print(f"{g.axes_dict = }")
        plt.show()



    def __getitem__(self, item):
        print(f"{item = }")
        c = self.data.loc[:, item].columns
        c2 = self.data.loc[:, (slice(None, None, None), ['gb', 'gbnsr6'], 'delta', 'EEL')].columns
        print(c, c2)
        mask = c2.isin(c)
        print(f"{mask = }")

    def get_data(self, unstacked=False):
        return self.data.unstack().reset_index().rename(columns={0: 'energy'}) if unstacked else self.data

    def plot(self, col='subsystem', row='component', sharey='row', x='term', y='energy', hue='method'):
        df = self.data.iloc[
            self.data.index.isin(['Average'])
        ].unstack().reset_index().rename(columns={0: 'energy'})

        g = sns.catplot(df, x=x, y=y, hue=hue, col=col, row=row, kind='bar',
                        sharey=sharey)
        # g.map(sns.barplot, "term", "energy", 'method')
        for axl, ax in g.axes_dict.items():
            ax.bar_label(ax.containers[0], fmt='%.2f', color=sns.color_palette()[0])
            ax.bar_label(ax.containers[1], fmt='%.2f', color=sns.color_palette()[1])

        print(f"{g.axes_dict = }")
        plt.show()

    # def get_subsystem(self, subsystem):

    def get_method(self, include_subsystems=True, ):
        pass

    def get_subsystem(self, subsystem):
        pass


class EnthalpySubSystem():
    def __init__(self, name, keys, data):
        self.keys = keys
        self.data = data

    def get_data(self):
        return self.data.loc[self.keys]

    def plot(self):



class EnthalpySubset:
    def __init__(self):
        pass

    def plot(self):
        pass
        




class Entropy:
    def __init__(self, name, data, index_info):
        # self.data = pd.DataFrame(flatten(data), index=index)
        pass

class BindingFreeEnergy:
    def __init__(self):
        pass
#
#
# """
# This module provides a means for users to take advantage of xBFreE's parsing
# ability. It exposes the free energy data (optionally to numpy arrays) so that
# users can write a simple script to carry out custom data analyses, leveraging
# the full power of Python's extensions, if they want (e.g., numpy, scipy, etc.)
# """
#
# # ##############################################################################
# #                           GPLv3 LICENSE INFO                                 #
# #                                                                              #
# #  Copyright (C) 2020  Mario S. Valdes-Tresanco and Mario E. Valdes-Tresanco   #
# #  Copyright (C) 2014  Jason Swails, Bill Miller III, and Dwight McGee         #
# #                                                                              #
# #   Project: https://github.com/Valdes-Tresanco-MS/gmx_MMPBSA                  #
# #                                                                              #
# #   This program is free software; you can redistribute it and/or modify it    #
# #  under the terms of the GNU General Public License version 3 as published    #
# #  by the Free Software Foundation.                                            #
# #                                                                              #
# #  This program is distributed in the hope that it will be useful, but         #
# #  WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY  #
# #  or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License    #
# #  for more details.                                                           #
# # ##############################################################################
# import logging
# import math
# import pickle
# import shutil
# import warnings
# from multiprocessing.pool import ThreadPool
# from copy import copy, deepcopy
# from typing import Union
#
# from xBFreE.mmpbsa.calculation import InteractionEntropyCalc, C2EntropyCalc
#
# from xBFreE.mmpbsa import infofile, main
# from xBFreE.exceptions import NoFileExists
# from xBFreE.fake_mpi import MPI
# from xBFreE.mmpbsa.output.amber import IEout, C2out
# import pandas as pd
# from pathlib import Path
# import os
# from types import SimpleNamespace
#
# from xBFreE.mmpbsa.utils.energy import emapping, flatten, get_std
# from xBFreE.utils.molecule import mask2list
#
#
# def _remove_empty_charts(data):
#     if isinstance(data, pd.Series):
#         if (data.abs() < 0.01).all():
#             return True
#     elif (data.abs() < 0.01).all().all():
#         return True
#
#
# def _itemdata_properties(data, decomp=False):
#     """
#     Pre-processing the items data.
#     Get the following properties:
#     - separable: if contains subcategories (DH [energetics components], Per-residue[receptor and ligand])
#
#     Also, remove empty terms and charts according to selected options
#     @param data:
#     @return:
#     """
#     groups = {}
#     if not decomp:
#         _extracted_from__itemdata_properties_5(data, groups)
#     else:
#         groups['Receptor'] = []
#         groups['Ligand'] = []
#         for k in data.columns:
#             if k[0].startswith('R:') and k[0] not in groups['Receptor']:
#                 groups['Receptor'].append(k[0])
#             elif k[0].startswith('L:') and k[0] not in groups['Ligand']:
#                 groups['Ligand'].append(k[0])
#     return groups
#
#
# # TODO Rename this here and in `_itemdata_properties`
# def _extracted_from__itemdata_properties_5(data, groups):
#     sep_ggas_keys = []
#     sep_gsolv_keys = []
#     # remove empty charts? (BOND, ANGLE and DIHEDRAL for ST)
#     # FIXME: NLPBsolver ?
#     ggas_keys = ['BOND', 'ANGLE', 'DIHED', 'VDWAALS', 'EEL', '1-4 VDW', '1-4 EEL', 'UB', 'IMP', 'CMAP', 'ESCF']
#     gsolv_keys = ['EGB', 'ESURF', 'EPB', 'ENPOLAR', 'EDISPER', 'POLAR SOLV', 'APOLAR SOLV', 'ERISM']
#     for k in data.columns:
#         if k in ggas_keys:
#             sep_ggas_keys.append(k)
#         elif k in gsolv_keys:
#             sep_gsolv_keys.append(k)
#     if sep_ggas_keys:
#         groups['GGAS'] = sep_ggas_keys
#         groups['GSOLV'] = sep_gsolv_keys
#         groups['TOTAL'] = ['GGAS', 'GSOLV', 'TOTAL']
#
#
# def _setup_data(data: pd.DataFrame, level=0, iec2=False, name=None, index=None,
#                 memory: dict = None, id=None):
#     # this variable show if the data changed or not. At first time, it is true, then when plotting become in false
#     change = True
#
#     inmemory: bool = memory.get('inmemory', False)
#     temp_path: Path = memory.get('temp_path')
#     parquet_file = temp_path.joinpath('_'.join(id) + '_%s').as_posix()
#
#     cont = {'line_plot_data': None, 'bar_plot_data': None, 'heatmap_plot_data': None}
#     if level == 0:
#         options = {'iec2': iec2}
#         data.name = data.name[-1]
#         line_plot_data = data[:-3].to_frame()
#         if inmemory:
#             cont['line_plot_data'] = [line_plot_data, options, change]
#         else:
#             line_plot_data.to_parquet(parquet_file % 'lp', compression=None)
#             cont['line_plot_data'] = [parquet_file % 'lp', options, change]
#     elif level == 1:
#         options = ({'iec2': True} if iec2 else {}) | {
#             'groups': _itemdata_properties(data)
#         }
#         bar_plot_data = data[-3:].reindex(columns=index)
#         if inmemory:
#             cont['bar_plot_data'] = [bar_plot_data, options, change]
#         else:
#             bar_plot_data.to_parquet(parquet_file % 'bp', compression=None)
#             cont['bar_plot_data'] = [parquet_file % 'bp', options, change]
#     elif level == 1.5:
#         options = {'iec2': True}
#         line_plot_data = data[['AccIntEnergy', 'ie']][:-3]
#         bar_plot_data = data[['ie', 'sigma']][-3:]
#         if inmemory:
#             cont['line_plot_data'] = [line_plot_data, options, change]
#             cont['bar_plot_data'] = [bar_plot_data, options, change]
#         else:
#             line_plot_data.to_parquet(parquet_file % 'lp', compression=None)
#             bar_plot_data.to_parquet(parquet_file % 'bp', compression=None)
#             cont['line_plot_data'] = [parquet_file % 'lp', options, change]
#             cont['bar_plot_data'] = [parquet_file % 'bp', options, change]
#
#     elif level == 2:
#         tempdf = data.loc[:, data.columns.get_level_values(1) == 'tot'].droplevel(level=1, axis=1)
#         temp_data = tempdf.reindex(columns=index)
#         line_plot_data = temp_data[:-3].sum(axis=1).rename(name).to_frame()
#         bar_plot_data = tempdf[-3:]
#         heatmap_plot_data = tempdf[:-3].T
#         if memory:
#             cont['line_plot_data'] = [line_plot_data, {}, change]
#             cont['bar_plot_data'] = [bar_plot_data, dict(groups=_itemdata_properties(bar_plot_data)), change]
#             cont['heatmap_plot_data'] = [heatmap_plot_data, {}, change]
#         else:
#             line_plot_data.to_parquet(parquet_file % 'lp', compression=None)
#             bar_plot_data.to_parquet(parquet_file % 'bp', compression=None)
#             heatmap_plot_data.to_parquet(parquet_file % 'hp', compression=None)
#             cont['line_plot_data'] = [parquet_file % 'lp', {}, change]
#             cont['bar_plot_data'] = [parquet_file % 'bp', dict(groups=_itemdata_properties(bar_plot_data)), change]
#             cont['heatmap_plot_data'] = [parquet_file % 'hp', {}, change]
#     elif level == 3:
#         # Select only the "tot" column, remove the level, change first level of columns to rows and remove the mean
#         # index
#         tempdf = data.loc[:, data.columns.get_level_values(2) == 'tot']
#         line_plot_data = tempdf[:-3].groupby(axis=1, level=0, sort=False).sum().reindex(
#             columns=index).sum(axis=1).rename(name).to_frame()
#         bar_plot_data = tempdf[:-3].groupby(axis=1, level=0, sort=False).sum().agg(
#             [lambda x: x.mean(), lambda x: x.std(ddof=0), lambda x: x.std(ddof=0) / math.sqrt(len(x))]
#         ).reindex(columns=index)
#         bar_plot_data.index = ['Average', 'SD', 'SEM']
#         heatmap_plot_data = tempdf.loc[["Average"]].droplevel(level=2, axis=1).stack().droplevel(level=0).reindex(
#             columns=index, index=index)
#         if memory:
#             cont['line_plot_data'] = [line_plot_data, {}, change]
#             cont['bar_plot_data'] = [bar_plot_data, dict(groups=_itemdata_properties(bar_plot_data)), change]
#             cont['heatmap_plot_data'] = [heatmap_plot_data, {}, change]
#         else:
#             line_plot_data.to_parquet(parquet_file % 'lp', compression=None)
#             bar_plot_data.to_parquet(parquet_file % 'bp', compression=None)
#             heatmap_plot_data.to_parquet(parquet_file % 'hp', compression=None)
#             cont['line_plot_data'] = [parquet_file % 'lp', {}, change]
#             cont['bar_plot_data'] = [parquet_file % 'bp', dict(groups=_itemdata_properties(bar_plot_data)), change]
#             cont['heatmap_plot_data'] = [parquet_file % 'hp', {}, change]
#
#     return cont
#
#
# def calculatestar(arg):
#     func, args, id, t = arg
#     data = args.get('data')
#     level = args.get('level', 0)
#     iec2 = args.get('iec2', False)
#     name = args.get('name')
#     index = args.get('index')
#     memory = args.get('memory')
#     return t, id, func(data, level, iec2, name, index, memory, id)
#
#
# class MMPBSA_API():
#     """ Main class that holds all the Free Energy data """
#
#     def __init__(self, settings: dict = None, t=None):
#         self.print_keys = None
#         self.app_namespace = None
#         self.raw_energy = None
#         self.data = {}
#         self.fname = None
#         self.settings = settings
#         self.temp_folder = None
#
#         self.result_data = {'normal': {'energy': {'enthalpy': {}, 'entropy': {}, 'binding_energy': {}},
#                                        'decomp_energy': {}},
#                             'mutant': {'energy': {'enthalpy': {}, 'entropy': {}, 'binding_energy': {}},
#                                        'decomp_energy': {}},
#                             'mutant-normal': {'energy': {'enthalpy': {}, 'entropy': {}, 'binding_energy': {}},
#                                               'decomp_energy': {}}}
#         self.keyword_map = deepcopy(self.result_data)
#
#         self._settings = {'data_on_disk': False, 'create_temporal_data': True, 'use_temporal_data': True,
#                           'overwrite_temp': True}
#         if settings:
#             not_keys = []
#             for k, v in settings.items():
#                 if k not in self._settings:
#                     not_keys.append(k)
#                     continue
#                 self._settings[k] = v
#             if not_keys:
#                 logging.warning(f'Not keys {not_keys}. Will be ignored')
#
#     def setting_time(self, timestart=0, timestep=0, timeunit='ps'):
#         self.starttime = timestart
#         self.timestep = timestep
#         self.timeunit = timeunit
#
#     def load_file(self, fname: Union[Path, str] = None):
#         """
#
#         Args:
#             fname: String- or Path-like file reference
#
#         Returns:
#
#         """
#         if not fname and not self.fname:
#             raise
#
#         if not self.fname:
#             self.fname = fname if isinstance(fname, Path) else Path(fname)
#             if not self.fname.exists():
#                 raise NoFileExists(f"cannot find {self.fname}!")
#             os.chdir(self.fname.parent)
#
#         self._get_fromBinary(self.fname)
#
#     def get_info(self):
#         """
#         Get all variables in the INFO dictionary
#         Returns:
#
#         """
#         return self.app_namespace.INFO
#
#     def get_input(self):
#         """
#         Get all variables defined in the INPUT dictionary
#         Returns:
#
#         """
#         return self.app_namespace.INPUT
#
#     def get_files(self):
#         """
#         Get all variables in the FILES dictionary
#         Returns:
#
#         """
#         return self.app_namespace.FILES
#
#     def _get_frames_index(self, framestype, startframe, endframe, interval):
#
#         if framestype == 'energy':
#             start = list(self.frames.keys()).index(startframe) if startframe else startframe
#             end = list(self.frames.keys()).index(endframe) + 1 if endframe else endframe
#             index_frames = {f: self.frames[f] for f in list(self.frames.keys())[start:end:interval]}
#         else:
#             start = list(self.nmframes.keys()).index(startframe) if startframe else startframe
#             end = list(self.nmframes.keys()).index(endframe) + 1 if endframe else endframe
#             index_frames = {f: self.nmframes[f] for f in list(self.nmframes.keys())[start:end:interval]}
#         return (start, end, pd.Series(index_frames.values(), name=f'Time ({self.timeunit})') if self.timestep
#         else pd.Series(index_frames.keys(), name='Frames'))
#
#     @staticmethod
#     def arg2tuple(arg):
#         return arg if isinstance(arg, tuple) else tuple(arg)
#
#     def _get_energy(self, startframe=None, endframe=None, interval=1, verbose=True):
#         """
#         Get energy
#         Args:
#             keys: Energy levels
#
#         Returns: Energy pd.Dataframe
#
#         """
#         s, e, index = self._get_frames_index('energy', startframe, endframe, interval)
#
#         summ_df = {}
#         temp_print_keys = tuple(x for x in ['normal', 'mutant', 'mutant-normal'] if x in self.data)
#
#         for et in temp_print_keys:
#             if et not in self.data:
#                 if verbose:
#                     warnings.warn(f'Not etype {et} in data')
#             elif not self.data[et]:
#                 continue
#             else:
#                 # energy[et] = {'enthalpy': {}}
#                 summ_df[et] = {'enthalpy': {}}
#                 temp_model_keys = tuple(x for x in self.data[et].keys() if x not in ['nmode', 'qh', 'ie', 'c2'])
#                 models_energy = {}
#                 for m in temp_model_keys:
#                     if m in self.data[et]:
#                         # print(f"{m = }, {self.keyword_map[et]['energy']['enthalpy'] = }")
#                         self.keyword_map[et]['energy']['enthalpy'][m] = {}
#                         models_energy[m] = {}
#                         temp_mol_keys = tuple(self.data[et][m].keys())
#
#                         for m1 in temp_mol_keys:
#                             if m1 in self.data[et][m]:
#                                 self.keyword_map[et]['energy']['enthalpy'][m][m1] = []
#                                 models_energy[m][m1] = {}
#                                 temp_terms_keys = tuple(self.data[et][m][m1].keys())
#                                 valid_terms = []
#
#                                 for t in temp_terms_keys:
#                                     if t not in self.data[et][m][m1]:
#                                         if verbose:
#                                             warnings.warn(f'Not term {t} in etype {et} > model {m} > mol {m1}')
#                                         continue
#                                     self.keyword_map[et]['energy']['enthalpy'][m][m1].append(t)
#                                     models_energy[m][m1][t] = self.data[et][m][m1][t][s:e:interval]
#                                     valid_terms.append(t)
#                             elif verbose:
#                                 warnings.warn(f'Not mol {m1} in etype {et} > model {m}')
#
#                     elif verbose:
#                         warnings.warn(f'Not model {m} in etype {et}')
#                 self.result_data[et]['energy']['enthalpy'], summ_df[et]['enthalpy'] = self._model2df(models_energy,
#                                                                                                      index,
#                                                                                                      ['method',
#                                                                                                       'component',
#                                                                                                       'term'])
#
#             # print(summ_df[et]['enthalpy'].iloc[:, ((summ_df[et]['enthalpy'].columns.get_level_values(1)=='delta') &
#             #                                       (summ_df[et]['enthalpy'].columns.get_level_values(2)=='TOTAL'))
#             #       ].droplevel([1, 2], axis=1).T.reset_index()
#             #       )
#         corr = {}
#         for et, v in summ_df.items():
#             corr[et] = {'enthalpy': {}}
#             for m, v2 in v.items():
#                 if 'delta' in v2:
#                     corr[et]['enthalpy'][m] = pd.DataFrame(
#                         {('ΔGeff', t): v for t, v in v2['delta']['TOTAL'].to_dict().items()}, index=[0])
#         return {'map': self.keyword_map, 'data': self.result_data, 'summary': summ_df, 'correlation': corr}
#
#     def get_energy(self, etype: tuple = None, model: tuple = None, mol: tuple = None, term: tuple = None,
#                    remove_empty_terms=True, threshold=0.01, startframe=None, endframe=None, interval=1, verbose=True):
#         """
#         Get energy
#         Args:
#             keys: Energy levels
#
#         Returns: Energy pd.Dataframe
#
#         """
#         # get start and end for frames range
#         if etype:
#             etype = self.arg2tuple(etype)
#         if model:
#             model = self.arg2tuple(model)
#         if mol:
#             mol = self.arg2tuple(mol)
#         if term:
#             term = self.arg2tuple(term)
#         s, e, index = self._get_frames_index('energy', startframe, endframe, interval)
#         e_map = {}
#         energy = {}
#         summ_df = {}
#         temp_print_keys = etype or tuple(x for x in ['normal', 'mutant', 'mutant-normal'] if x in self.data)
#
#         for et in temp_print_keys:
#             if et not in self.data:
#                 if verbose:
#                     warnings.warn(f'Not etype {et} in data')
#             elif not self.data[et]:
#                 continue
#             else:
#                 e_map[et] = {}
#                 energy[et] = {}
#                 summ_df[et] = {}
#                 temp_model_keys = model or tuple(
#                     x for x in self.data[et].keys() if x not in ['nmode', 'qh', 'ie', 'c2'])
#
#                 for m in temp_model_keys:
#                     if m in self.data[et]:
#                         e_map[et][m] = {}
#                         model_energy = {}
#                         temp_mol_keys = mol or tuple(self.data[et][m].keys())
#
#                         for m1 in temp_mol_keys:
#                             if m1 in self.data[et][m]:
#                                 e_map[et][m][m1] = []
#                                 model_energy[m1] = {}
#                                 temp_terms_keys = ([x for x in self.data[et][m][m1].keys() if x in term] if term
#                                                    else tuple(self.data[et][m][m1].keys()))
#                                 valid_terms = []
#
#                                 for t in temp_terms_keys:
#                                     if t not in self.data[et][m][m1]:
#                                         if verbose:
#                                             warnings.warn(f'Not term {t} in etype {et} > model {m} > mol {m1}')
#                                     elif (
#                                             not remove_empty_terms
#                                             or abs(self.data[et][m][m1][t].mean())
#                                             >= threshold or t in ['GSOLV', 'GGAS', 'TOTAL']
#                                     ):
#                                         e_map[et][m][m1].append(t)
#                                         model_energy[m1][t] = self.data[et][m][m1][t][s:e:interval]
#                                         valid_terms.append(t)
#                             elif verbose:
#                                 warnings.warn(f'Not mol {m1} in etype {et} > model {m}')
#                         energy[et][m], summ_df[et][m] = self._model2df(model_energy, index)
#
#                     elif verbose:
#                         warnings.warn(f'Not model {m} in etype {et}')
#         corr = {}
#         for et, v in summ_df.items():
#             corr[et] = {}
#             for m, v2 in v.items():
#                 if 'delta' in v2:
#                     corr[et][m] = pd.DataFrame(
#                         {('ΔGeff', t): v for t, v in v2['delta']['TOTAL'].to_dict().items()}, index=[0])
#         return {'map': e_map, 'data': energy, 'summary': summ_df, 'correlation': corr}
#
#     def _model2df(self, energy, index, multiindex_names=None):
#         energy_df = pd.DataFrame(flatten(energy), index=index)
#         if multiindex_names:
#             energy_df.columns.names = multiindex_names
#         # print(energy_df.columns.names)
#         s = pd.concat([energy_df.mean().round(3),
#                        energy_df.std(ddof=0).round(3),
#                        (energy_df.std(ddof=0) / math.sqrt(len(index))).round(3)],
#                       axis=1)
#         s.columns = ['Average', 'SD', 'SEM']
#         summary_df = s.T
#         df = pd.concat([energy_df, summary_df])
#         df.index.name = index.name
#         return df, summary_df
#
#     def get_nmode_entropy(self, nmtype: tuple = None, mol: tuple = None, term: tuple = None,
#                           startframe=None, endframe=None, interval=None, verbose=True):
#
#         s, e, index = self._get_frames_index('entropy', startframe, endframe, interval)
#
#         energy = {}
#         summ_df = {}
#         temp_print_keys = nmtype or tuple(x for x in ['normal', 'mutant', 'mutant-normal'] if x in self.data and
#                                           self.data[x])
#         for et in temp_print_keys:
#             if et in self.data:
#                 energy[et] = {'nmode': {}}
#                 summ_df[et] = {'nmode': {}}
#                 model_energy = {}
#                 temp_mol_keys = mol or tuple(self.data[et]['nmode'].keys())
#                 for m1 in temp_mol_keys:
#                     if m1 in self.data[et]['nmode']:
#                         model_energy[m1] = {}
#                         temp_terms_keys = ([x for x in self.data[et]['nmode'][m1].keys() if x in term] if term
#                                            else tuple(self.data[et]['nmode'][m1].keys()))
#                         valid_terms = []
#                         for t in temp_terms_keys:
#                             if t in self.data[et]['nmode'][m1]:
#                                 model_energy[m1][t] = self.data[et]['nmode'][m1][t][s:e:interval]
#                                 valid_terms.append(t)
#                             elif verbose:
#                                 warnings.warn(f'Not term {t} in etype {et} > mol {m1}')
#                     elif verbose:
#                         warnings.warn(f'Not mol {m1} in etype {et}')
#                 energy[et]['nmode'], summ_df[et]['nmode'] = self._model2df(model_energy, index)
#
#             elif verbose:
#                 warnings.warn(f'Not nmtype {et} in data')
#         return {'map': emapping(energy), 'data': energy, 'summary': summ_df}
#
#     def get_qh_entropy(self, qhtype: tuple = None, mol: tuple = None, term: tuple = None, verbose=True):
#         temp_print_keys = qhtype or tuple(x for x in ['normal', 'mutant', 'mutant-normal'] if x in self.data)
#         entropy = {}
#         for et in temp_print_keys:
#             if et in self.data:
#                 entropy[et] = {'qh': {}}
#                 temp_mol_keys = mol or tuple(self.data[et]['qh'].keys())
#                 for m1 in temp_mol_keys:
#                     if m1 in self.data[et]['qh']:
#                         entropy[et]['qh'][m1] = {}
#                         temp_terms_keys = ([x for x in self.data[et]['qh'][m1].keys() if x in term] if term
#                                            else tuple(self.data[et]['qh'][m1].keys()))
#                         for t in temp_terms_keys:
#                             if t in self.data[et]['qh'][m1]:
#                                 entropy[et]['qh'][m1][t] = self.data[et]['qh'][m1][t]
#
#                             elif verbose:
#                                 warnings.warn(f'Not term {t} in etype {et} > mol {m1}')
#                     elif verbose:
#                         warnings.warn(f'Not mol {m1} in qhtype {et}')
#             elif verbose:
#                 warnings.warn(f'Not qhtype {et} in data')
#         df = pd.DataFrame(flatten(entropy))
#         return {'map': emapping(entropy), 'data': df, 'summary': df.xs(('delta', 'TOTAL'), level=[1, 2], axis=1)}
#
#     def get_c2_entropy(self, c2type: tuple = None, startframe=None, endframe=None, interval=None, verbose=True):
#         temp_print_keys = c2type or tuple(x for x in ['normal', 'mutant', 'mutant-normal'] if x in self.data and
#                                           self.data[x])
#         entropy = {}
#         entropy_df = {}
#         recalc = bool((startframe and startframe != self.app_namespace.INPUT['general']['startframe'] or
#                        endframe and endframe != self.app_namespace.INPUT['general']['endframe'] or
#                        interval and interval != self.app_namespace.INPUT['general']['interval']))
#
#         for et in temp_print_keys:
#             if et not in self.data and verbose:
#                 warnings.warn(f'Not c2type {et} in data')
#             if recalc:
#                 d = self._recalc_iec2('c2', et, startframe, endframe, interval)
#             else:
#                 d = self.data[et]['c2']
#
#             entropy[et] = {'c2': {}}
#             entropy_df[et] = {'c2': {}}
#
#             for emodel in d:
#                 entropy[et]['c2'][emodel] = {x: None for x in ['c2', 'sigma']}
#                 entropy_df[et]['c2'][emodel] = pd.DataFrame({'c2': [d[emodel]['c2data'], d[emodel]['c2_std'],
#                                                                     d[emodel]['c2_std']],
#                                                              'sigma': [d[emodel]['sigma'], 0, 0]},
#                                                             index=['Average', 'SD', 'SEM'])
#         return {'map': emapping(entropy), 'data': entropy_df, 'summary': entropy_df}
#
#     def get_ie_entropy(self, ietype: tuple = None, startframe=None, endframe=None, interval=None,
#                        ie_segment=25, verbose=True):
#         temp_print_keys = ietype or tuple(x for x in ['normal', 'mutant', 'mutant-normal'] if x in self.data and
#                                           self.data[x])
#         entropy = {}
#         summ_df = {}
#         entropy_df = {}
#         recalc = bool((startframe and startframe != self.app_namespace.INPUT['general']['startframe'] or
#                        endframe and endframe != self.app_namespace.INPUT['general']['endframe'] or
#                        interval and interval != self.app_namespace.INPUT['general']['interval']))
#
#         s, e, index = self._get_frames_index('energy', startframe, endframe, interval)
#         for et in temp_print_keys:
#             if et not in self.data:
#                 if verbose:
#                     warnings.warn(f'Not ietype {et} in data')
#                 continue
#             if recalc:
#                 d = self._recalc_iec2('ie', et, startframe, endframe, interval, ie_segment)
#             else:
#                 d = self.data[et]['ie']
#
#             entropy[et] = {'ie': {}}
#             summ_df[et] = {'ie': {}}
#             entropy_df[et] = {'ie': {}}
#
#             for emodel in d:
#                 ieframes = math.ceil(len(d[emodel]['data']) * ie_segment / 100)
#                 entropy[et]['ie'][emodel] = {x: None for x in ['AccIntEnergy', 'ie', 'sigma']}
#
#                 df = pd.DataFrame({'AccIntEnergy': d[emodel]['data']}, index=index)
#                 df1 = pd.DataFrame({'ie': d[emodel]['data'][-ieframes:]}, index=index[-ieframes:])
#                 df2 = pd.concat([df, df1], axis=1)
#                 df3 = pd.DataFrame({'ie': [float(d[emodel]['iedata'].mean()),
#                                            float(d[emodel]['iedata'].std()),
#                                            float(d[emodel]['iedata'].std() / math.sqrt(ieframes))],
#                                     'sigma': [d[emodel]['sigma'], 0, 0]}, index=['Average', 'SD', 'SEM'])
#                 summ_df[et]['ie'][emodel] = df3
#                 df4 = pd.concat([df2, df3])
#                 df4.index.name = df.index.name
#                 entropy_df[et]['ie'][emodel] = df4
#         return {'map': emapping(entropy), 'data': entropy_df, 'summary': summ_df}
#
#     @staticmethod
#     def _merge_ent(res_dict: dict, d: dict):
#         for e1, v1 in d.items():
#             if e1 not in res_dict:
#                 res_dict[e1] = v1
#             else:
#                 res_dict[e1].update(v1)
#
#     def get_entropy(self, etype: tuple = None, model: tuple = None, mol: tuple = None, term: tuple = None,
#                     nmstartframe=None, nmendframe=None, nminterval=1, startframe=None, endframe=None, interval=None,
#                     ie_segment=25, verbose=True):
#         temp_print_keys = etype or tuple(x for x in ['normal', 'mutant', 'mutant-normal'] if x in self.data)
#         entropy_keys = []
#
#         for et in temp_print_keys:
#             if et in self.data:
#                 entropy_keys.extend(x for x in self.data[et].keys() if x in ['nmode', 'qh', 'ie', 'c2'])
#             elif verbose:
#                 warnings.warn(f'Not etype {et} in data')
#         temp_model_keys = tuple(x for x in entropy_keys if x in model) if model else tuple(entropy_keys)
#
#         ent_summ = {}
#         ent_map = {}
#         ent_data = {}
#         for m in temp_model_keys:
#             if m == 'nmode':
#                 _m, _d, _s = self.get_nmode_entropy(etype, mol, term, nmstartframe, nmendframe, nminterval).values()
#             elif m == 'qh':
#                 _m, _d, _s = self.get_qh_entropy(etype, mol, term).values()
#             elif m == 'ie':
#                 _m, _d, _s = self.get_ie_entropy(etype, startframe, endframe, interval, ie_segment).values()
#             else:
#                 _m, _d, _s = self.get_c2_entropy(etype, startframe, endframe, interval).values()
#             self._merge_ent(ent_map, _m)
#             self._merge_ent(ent_data, _d)
#             self._merge_ent(ent_summ, _s)
#
#         return {'map': ent_map, 'data': ent_data, 'summary': ent_summ}
#
#     def _recalc_iec2(self, method, etype, startframe=None, endframe=None, interval=None, ie_segment=25):
#         allowed_met = ['gb', 'pb', 'rism std', 'rism gf', 'rism pcplus', 'gbnsr6']
#         result = {}
#         start = list(self.frames.keys()).index(startframe) if startframe else startframe
#         end = list(self.frames.keys()).index(endframe) + 1 if endframe else endframe
#         for key in allowed_met:
#             if key in self.data[etype]:
#                 edata = self.data[etype][key]['delta']['GGAS'][start:end:interval]
#                 if method == 'ie':
#                     ie = InteractionEntropyCalc(edata,
#                                                 {'general':
#                                                     dict(
#                                                         temperature=self.app_namespace.INPUT['general']['temperature'],
#                                                         startframe=startframe, endframe=endframe, interval=interval
#                                                     )},
#                                                 key, iesegment=ie_segment)
#                     result[key] = IEout({}, key)
#                     result[key].parse_from_dict(dict(data=ie.data, sigma=ie.ie_std, iedata=ie.iedata))
#                 else:
#                     c2 = C2EntropyCalc(edata, {'general':
#                                                    dict(temperature=self.app_namespace.INPUT['general'][
#                                                        'temperature'])}, key)
#                     result[key] = C2out(key)
#                     result[key].parse_from_dict(
#                         dict(c2data=c2.c2data, c2_std=c2.c2_std, sigma=c2.ie_std, c2_ci=c2.c2_ci))
#         return result
#
#     def get_binding(self, energy_summary=None, entropy_summary=None, verbose=True):
#         binding = {}
#         b_map = {}
#         corr = {}
#         if energy_summary and entropy_summary:
#             dg_string = {'ie': 'ΔGie', 'c2': 'ΔGc2', 'nmode': 'ΔGnm', 'qh': 'ΔGqh'}
#             for et, ev in energy_summary.items():
#                 binding[et] = {}
#                 b_map[et] = {}
#                 corr[et] = {}
#                 for em, emv in ev.items():
#                     binding[et][em] = {}
#                     b_map[et][em] = []
#                     mol = 'complex' if self.app_namespace.FILES.stability else 'delta'
#                     edata = emv[mol]['TOTAL']
#                     edata.name = 'ΔH'
#                     if et in entropy_summary:
#                         if mol == 'delta':
#                             corr[et][em] = {}
#                         c = {}
#                         for ent, etv in entropy_summary[et].items():
#                             b_map[et][em].append(ent)
#                             if ent == 'ie' and not self.app_namespace.FILES.stability:
#                                 entdata = etv[em]['ie']
#                             elif ent == 'c2' and not self.app_namespace.FILES.stability:
#                                 entdata = etv[em]['c2']
#                             else:
#                                 entdata = etv[mol]['TOTAL']
#                             entdata.name = '-TΔS'
#                             dg = edata.loc['Average'] + entdata.loc['Average']
#                             std = get_std(edata.loc['SD'], entdata.loc['SD'])
#                             dgdata = pd.Series([dg, std, std], index=['Average', 'SD', 'SEM'], name='ΔG')
#                             binding[et][em][ent] = pd.concat([edata, entdata, dgdata], axis=1)
#                             if mol == 'delta':
#                                 c[(dg_string[ent], 'Average')] = dg
#                                 c[(dg_string[ent], 'SD')] = std
#                                 c[(dg_string[ent], 'SEM')] = std
#                         if mol == 'delta':
#                             corr[et][em] = pd.DataFrame(c, index=[0])
#         return {'map': b_map, 'data': binding, 'correlation': corr}
#
#     def get_decomp_energy(self, etype: tuple = None, model: tuple = None, mol: tuple = None, contribution: tuple = None,
#                           res1: tuple = None, res2: tuple = None, term: tuple = None, res_threshold=0.5,
#                           startframe=None, endframe=None, interval=None, verbose=True):
#
#         s, e, index = self._get_frames_index('energy', startframe, endframe, interval)
#         name = index.name
#         index = pd.concat([index, pd.Series(['Average', 'SD', 'SEM'])])
#         index.name = name
#
#         temp_print_keys = etype or tuple(x for x in ['decomp_normal', 'decomp_mutant'] if self.data.get(x))
#         self.print_keys = []
#
#         decomp_energy = {}
#         e_map = {}
#         for et in temp_print_keys:
#             if not self.data.get(et):
#                 if verbose:
#                     warnings.warn(f'Not etype {et} in data')
#             else:
#                 etkey = et.split('_')[1]
#                 decomp_energy[etkey] = {}
#                 e_map[etkey] = {}
#                 temp_model_keys = model or tuple(self.data[et].keys())
#
#                 for m in temp_model_keys:
#                     if m not in self.data[et]:
#                         if verbose:
#                             warnings.warn(f'Not model {m} in etype {et}')
#                     else:
#                         model_decomp_energy = {}
#
#                         e_map[etkey][m] = {}
#                         temp_mol_keys = mol or tuple(self.data[et][m].keys())
#
#                         for m1 in temp_mol_keys:
#                             if m1 not in self.data[et][m]:
#                                 if verbose:
#                                     warnings.warn(f'Not mol {m1} in etype {et} > model {m}')
#                             else:
#                                 model_decomp_energy[m1] = {}
#                                 e_map[etkey][m][m1] = {}
#                                 temp_comp_keys = contribution or tuple(self.data[et][m][m1].keys())
#                                 for c in temp_comp_keys:
#                                     if c not in self.data[et][m][m1]:
#                                         if verbose:
#                                             warnings.warn(f'Not component {c} in etype {et} > model {m} > mol {m1}')
#                                     else:
#                                         model_decomp_energy[m1][c] = {}
#                                         e_map[etkey][m][m1][c] = {}
#                                         temp_res1_keys = res1 or tuple(self.data[et][m][m1][c].keys())
#
#                                         for r1 in temp_res1_keys:
#                                             remove = False
#                                             if r1 not in self.data[et][m][m1][c]:
#                                                 if verbose:
#                                                     warnings.warn(
#                                                         f'Not res {r1} in etype {et} > model {m} > mol {m1} > comp {c} ')
#                                             else:
#                                                 temp_energy = {}
#
#                                                 if self.app_namespace.INPUT['decomp']['idecomp'] in [1, 2]:
#                                                     temp_emap = []
#                                                     temp_terms_keys = term or tuple(self.data[et][m][m1][c][r1].keys())
#
#                                                     for t in temp_terms_keys:
#                                                         if t not in self.data[et][m][m1][c][r1]:
#                                                             if verbose:
#                                                                 warnings.warn(f'Not term {t} in etype {et} > model {m} '
#                                                                               f'> mol {m1} > comp {c} > res {r1}')
#                                                         else:
#                                                             temp_energy[t] = self.data[et][m][m1][c][r1][t][
#                                                                              s:e:interval]
#                                                             temp_emap.append(t)
#                                                             mean = temp_energy[t].mean()
#                                                             std = temp_energy[t].std()
#                                                             sem = std / math.sqrt(len(temp_energy[t]))
#                                                             temp_energy[t] = temp_energy[t].append([mean, std, sem])
#                                                             if (t == 'tot' and res_threshold > 0 and
#                                                                     abs(mean) < res_threshold):
#                                                                 remove = True
#                                                 else:
#                                                     temp_emap = {}
#                                                     temp_res2_keys = res2 or tuple(self.data[et][m][m1][c][r1].keys())
#                                                     # for per-wise only since for per-residue we get the tot value
#                                                     res1_contrib = 0
#                                                     for r2 in temp_res2_keys:
#                                                         if r2 not in self.data[et][m][m1][c][r1]:
#                                                             if verbose:
#                                                                 warnings.warn(f'Not res {r2} in etype {et} > model {m}'
#                                                                               f' > mol {m1} > comp {c} > res {r1}')
#                                                         else:
#                                                             temp_energy_r2 = {}
#                                                             temp_emap[r2] = []
#                                                             # energy[et][m][m1][c][r1][r2] = {}
#                                                             temp_terms_keys = term or tuple(
#                                                                 self.data[et][m][m1][c][r1][r2].keys())
#                                                             for t in temp_terms_keys:
#                                                                 if t not in self.data[et][m][m1][c][r1][r2]:
#                                                                     if verbose:
#                                                                         warnings.warn(
#                                                                             f'Not term {t} in etype {et} > model {m} '
#                                                                             f'> mol {m1} > comp {c} > res {r1} > res {r2}')
#                                                                 else:
#                                                                     temp_emap[r2].append(t)
#                                                                     temp_energy_r2[t] = self.data[et][m][m1][c][r1][
#                                                                                             r2][t][s:e:interval]
#                                                                     mean = temp_energy_r2[t].mean()
#                                                                     std = temp_energy_r2[t].std()
#                                                                     sem = std / math.sqrt(len(temp_energy_r2[t]))
#                                                                     temp_energy_r2[t] = temp_energy_r2[t].append([
#                                                                         mean, std, sem])
#                                                                     if t == 'tot':
#                                                                         res1_contrib += mean
#                                                             if temp_energy_r2:
#                                                                 temp_energy[r2] = temp_energy_r2
#                                                     if res_threshold > 0 and float(abs(res1_contrib)) < res_threshold:
#                                                         remove = True
#                                                 if not remove:
#                                                     model_decomp_energy[m1][c][r1] = temp_energy
#                                                     e_map[etkey][m][m1][c][r1] = temp_emap
#                                 # issue #269
#                                 if model_decomp_energy[m1].get('BDC') is not None:
#                                     model_decomp_energy[m1].pop('BDC')
#                                     e_map[etkey][m][m1].pop('BDC')
#                                     if verbose:
#                                         warnings.warn('Warning: Empty BDC component...')
#
#                         decomp_energy[etkey][m] = pd.DataFrame(flatten(model_decomp_energy), index=index)
#         return {'map': e_map, 'data': decomp_energy}
#
#     def get_ana_data(self, energy_options=None, entropy_options=None, decomp_options=None, performance_options=None,
#                      correlation=False, verbose=False):
#         TASKs = []
#         d = {}
#         corr = {}
#         ecorr = None
#         memory_args = dict(temp_path=self.temp_folder)
#         if energy_options:
#             energy_map, energy, energy_summary, ecorr = self.get_energy(**energy_options, verbose=verbose).values()
#             if energy_map:
#                 for et, v in ecorr.items():
#                     corr[et] = v
#                 d['enthalpy'] = {'map': energy_map, 'keys': {}, 'summary': energy_summary}
#                 memory_args['inmemory'] = performance_options.get('energy_memory')
#                 for level, value in energy_map.items():
#                     for level1, value1 in value.items():
#                         for level2, value2 in value1.items():
#                             TASKs.append([_setup_data, dict(data=energy[level][level1][level2][value2], level=1,
#                                                             memory=memory_args),
#                                           (level, level1, level2), 'enthalpy'])
#                             TASKs.extend([_setup_data, dict(data=energy[level][level1][(level2, level3)], level=0,
#                                                             memory=memory_args),
#                                           (level, level1, level2, level3), 'enthalpy'] for level3 in value2)
#
#         if entropy_options:
#             entropy_map, entropy, entropy_summary = self.get_entropy(**entropy_options, verbose=verbose).values()
#             if entropy_map:
#                 d['entropy'] = {'map': entropy_map, 'keys': {}, 'summary': entropy_summary}
#                 memory_args['inmemory'] = performance_options.get('energy_memory')
#                 for level, value in entropy_map.items():
#                     for level1, value1 in value.items():
#                         if level1 in ['nmode', 'qh']:
#                             for level2, value2 in value1.items():
#                                 TASKs.append([_setup_data, dict(data=entropy[level][level1][level2], level=1,
#                                                                 memory=memory_args),
#                                               (level, level1, level2), 'entropy'])
#                                 TASKs.extend([_setup_data, dict(data=entropy[level][level1][(level2, level3)],
#                                                                 level=0, memory=memory_args),
#                                               (level, level1, level2, level3), 'entropy'] for level3 in value2)
#                         elif level1 == 'c2':
#                             for level2, value2 in value1.items():
#                                 TASKs.append([_setup_data, dict(data=entropy[level][level1][level2], level=1, iec2=True,
#                                                                 memory=memory_args),
#                                               (level, level1, level2), 'entropy'])
#                         elif level1 == 'ie':
#                             for level2, value2 in value1.items():
#                                 TASKs.append([_setup_data, dict(data=entropy[level][level1][level2], level=1.5,
#                                                                 memory=memory_args),
#                                               (level, level1, level2), 'entropy'])
#
#         if energy_options and entropy_options:
#             bind_map, binding, bcorr = self.get_binding(energy_summary, entropy_summary, verbose=verbose).values()
#             if bind_map:
#                 for et, v in bcorr.items():
#                     for m, v1 in v.items():
#                         if ecorr:
#                             corr[et][m] = pd.concat([ecorr[et][m], v1], axis=1)
#
#                 d['binding'] = {'map': bind_map, 'keys': {}, 'summary': binding}
#                 memory_args['inmemory'] = performance_options.get('energy_memory')
#                 for level, value in bind_map.items():
#                     for level1, value1 in value.items():
#                         TASKs.extend([_setup_data, dict(data=binding[level][level1][level2], level=1,
#                                                         memory=memory_args),
#                                       (level, level1, level2), 'binding'] for level2 in value1)
#         if decomp_options:
#             decomp_map, decomp = self.get_decomp_energy(**decomp_options, verbose=verbose).values()
#             if decomp_map:
#                 d['decomposition'] = {'map': decomp_map, 'keys': {}}
#                 memory_args['inmemory'] = performance_options.get('decomp_memory')
#                 for level, value in decomp_map.items():
#                     for level1, value1 in value.items():
#                         for level2, value2 in value1.items():
#                             for level3, value3 in value2.items():
#                                 item_lvl = 2 if self.app_namespace.INPUT['decomp']['idecomp'] in [1, 2] else 3
#                                 index = list(value3.keys())
#                                 for level4, value4 in value3.items():
#                                     if item_lvl == 3 and len(index) == 1:
#                                         index.append(list(value4.keys()))
#                                     item_lvl2 = 1 if self.app_namespace.INPUT['decomp']['idecomp'] in [1, 2] else 2
#                                     if self.app_namespace.INPUT['decomp']['idecomp'] in [1, 2]:
#                                         TASKs.append(
#                                             [_setup_data, dict(data=decomp[level][level1][level2][level3][level4],
#                                                                level=item_lvl2, name=level4, index=value4,
#                                                                memory=memory_args),
#                                              (level, level1, level2, level3, level4), 'decomposition'])
#                                         TASKs.extend([_setup_data,
#                                                       dict(data=decomp[level][level1][level2][level3][level4][level5],
#                                                            memory=memory_args),
#                                                       (level, level1, level2, level3, level4, level5), 'decomposition']
#                                                      for level5 in value4)
#                                     else:
#                                         TASKs.append(
#                                             [_setup_data, dict(data=decomp[level][level1][level2][level3][level4],
#                                                                level=item_lvl2, name=level4, index=list(value4.keys()),
#                                                                memory=memory_args),
#                                              (level, level1, level2, level3, level4), 'decomposition'])
#                                         TASKs.extend([_setup_data,
#                                                       dict(data=decomp[level][level1][level2][level3][level4][level5],
#                                                            level=1, index=value5, memory=memory_args),
#                                                       (level, level1, level2, level3, level4, level5), 'decomposition']
#                                                      for level5, value5 in value4.items())
#                                 TASKs.append([_setup_data,
#                                               dict(data=decomp[level][level1][level2][level3], level=item_lvl,
#                                                    name=level3, index=index, memory=memory_args),
#                                               (level, level1, level2, level3), 'decomposition'])
#
#         with ThreadPool(performance_options.get('jobs')) as pool:
#             imap_unordered_it = pool.imap_unordered(calculatestar, TASKs)
#             for t, id, result in imap_unordered_it:
#                 d[t]['keys'][id] = result
#
#         if correlation:
#             d['correlation'] = corr
#
#         return d
#
#     def _get_fromBinary(self, ifile):
#         with open(ifile, 'rb') as bf:
#             info = pickle.load(bf)
#             self.app_namespace = self._get_namespace(info, 'Binary')
#             bdata = pickle.load(bf)
#             self._oringin = {'normal': bdata.normal, 'mutant': bdata.mutant, 'decomp_normal': bdata.decomp_normal,
#                              'decomp_mutant': bdata.decomp_mutant, 'mutant-normal': bdata.mut_norm}
#             self._finalize_reading(ifile)
#             print(bdata.normal)
#
#     def _finalize_reading(self, ifile):
#         self.temp_folder = ifile.parent.joinpath('.gmx_mmpbsa_temp')
#         if self.temp_folder.exists():
#             shutil.rmtree(self.temp_folder)
#         self.temp_folder.mkdir()
#         self.data = copy(self._oringin)
#         self._get_frames()
#
#     @staticmethod
#     def _get_namespace(app, tfile):
#
#         if tfile == 'App':
#             com_pdb = ''.join(open(app.FILES.complex_fixed).readlines())
#             input_file = app.input_file_text
#             output_file = ''.join(open(app.FILES.output_file).readlines())
#             decomp_output_file = ''.join(open(app.FILES.decompout).readlines()) if app.INPUT['decomp']['decomprun'] \
#                 else None
#             size = app.mpi_size
#         else:
#             com_pdb = app.COM_PDB
#             input_file = app.input_file
#             output_file = app.output_file
#             decomp_output_file = app.decomp_output_file if app.INPUT['decomp']['decomprun'] else None
#             size = app.size
#             # write the pdb file
#             with open(app.FILES.complex_fixed, 'w') as opdb:
#                 opdb.write(app.COM_PDB)
#             app.resl = mask2list(app.FILES.complex_fixed, app.INPUT['general']['receptor_mask'],
#                                  app.INPUT['general']['ligand_mask'])
#
#         INFO = {'COM_PDB': com_pdb,
#                 'input_file': input_file,
#                 'mutant_index': app.mutant_index,
#                 'mut_str': app.resl[app.mutant_index].mutant_label if app.mutant_index is not None else '',
#                 'numframes': app.numframes,
#                 'numframes_nmode': app.numframes_nmode,
#                 'output_file': output_file,
#                 'size': size,
#                 'using_chamber': app.using_chamber,
#                 'decomp_output_file': decomp_output_file}
#
#         return SimpleNamespace(FILES=app.FILES, INPUT=app.INPUT, INFO=INFO)
#
#     def _get_frames(self):
#
#         ts = self.timestep or 1
#
#         INPUT = self.app_namespace.INPUT
#         numframes = self.app_namespace.INFO['numframes']
#         nmnumframes = self.app_namespace.INFO['numframes_nmode']
#
#         frames_list = list(range(INPUT['general']['startframe'],
#                                  INPUT['general']['startframe'] + numframes * INPUT['general']['interval'],
#                                  INPUT['general']['interval']))
#         self.frames_list = frames_list
#         INPUT['general']['endframe'] = frames_list[-1]
#         time_step_list = list(range(self.starttime,
#                                     self.starttime + len(frames_list) * ts * INPUT['general']['interval'],
#                                     ts * INPUT['general']['interval']))
#         self.frames = dict(zip(frames_list, time_step_list))
#
#         if INPUT['nmode']['nmoderun']:
#             nmframes_list = list(range(INPUT['nmode']['nmstartframe'],
#                                        INPUT['nmode']['nmstartframe'] + nmnumframes * INPUT['nmode']['nminterval'],
#                                        INPUT['nmode']['nminterval']))
#             INPUT['nmode']['nmendframe'] = nmframes_list[-1]
#
#             nm_start = (nmframes_list[0] - frames_list[0]) * INPUT['general']['interval']
#             nmtime_step_list = list(range(self.starttime + nm_start,
#                                           self.starttime + nm_start + len(nmframes_list) * ts * INPUT['nmode'][
#                                               'nminterval'],
#                                           ts * INPUT['nmode']['nminterval']))
#             self.nmframes_list = nmframes_list
#             self.nmframes = dict(zip(nmframes_list, nmtime_step_list))
#
# # mmpbsa = MMPBSA_API({'data_on_disk': True})
# # mmpbsa.setting_time()
# # mmpbsa.load_file("/home/mario/Documents/xBFreE_test/1.x.x/examples/gmx_example/COMPACT_RESULTS_MMPBSA.xbfree")
# #
# # f = mmpbsa._get_energy()['data']['normal']['energy']['enthalpy'].unstack().reset_index().rename(columns={0: 'energy'})
# # f1 = mmpbsa._get_energy()
# # f2 = mmpbsa._get_energy()['data']['normal']['energy']['enthalpy']
# # print(f)
# # print(f.memory_usage(deep=True))
# # print(f.dtypes)
# # fc = f.copy()
# # to_conv = ['method', 'component', 'term']
# # fc[to_conv] = fc[to_conv].astype("category")
# # fc['energy'] = fc['energy'].apply(pd.to_numeric, downcast="float")
# # # fc['Frames'] = fc['Frames'].apply(pd.to_numeric, downcast="integer", errors='ignore')
# # print(fc.memory_usage(deep=True))
# # print(fc.dtypes)
# #
# # reduction = fc.memory_usage(deep=True).sum() / f.memory_usage(deep=True).sum()
# # print(f"{reduction:0.2f}")
# #
# # # print('###############################')
# # # from pandas import IndexSlice as idx
# # # cols = idx['gb', 'delta', ['GSOLV', 'TOTAL']]
# # # print(f1['data']['normal']['energy']['enthalpy'].loc[:, cols])
# # # ggg = mmpbsa.get_ana_data(**{'energy_options': {'etype': ('normal',), 'mol': ('delta',)},
# # #                      'entropy_options': {'etype': ('normal',), 'mol': ('delta',)},
# # #                      'decomp_options': {'res_threshold': 0.5, 'etype': ('decomp_normal',), 'mol': ('delta',)},
# # #                      'correlation': False,
# # #                      'performance_options': {'energy_memory': False, 'decomp_memory': True, 'jobs': 12}})
# # # print(ggg)

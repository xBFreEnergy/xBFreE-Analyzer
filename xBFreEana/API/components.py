import pickle
from pathlib import Path
import hashlib
import pandas as pd
from typing import Union
import os

from xBFreEana.API.mmpbsa import MMPBSACalculation


class xBFreEAPI:
    def __init__(self):
        self.systems = CalculationSystems()
        pass

    def load_files(self, files: Union[list[str, Path], list[str], list[Path], str, Path]):
        """"""
        systems = {}
        # # FIXME: use hash to identify if multiples methods belongs to the same system
        # if isinstance(file, list):
        #     for f in file:
        #         fp = Path(f)
        #         if fp.exists():
        #             if fp.is_file():
        #                 pass
        #             else:
        if not isinstance(files, list):
            files = [files]
        for file in files:
            with open(file, 'rb') as bf:
                sysinfo = pickle.load(bf)
                print(sysinfo)

                if not isinstance(sysinfo, dict):
                    raise TypeError('This file was generated with gmx_MMPBSA. Please, execute xbfree gmx_MMPBSA '
                                    '--rewrite-output to generate compatible files')

                sysid = sysinfo.get('hash')
                sys_name = sysinfo.get('name')
                method = sysinfo.get('method')

                if method == 'mmpbsa':
                    MethodClass = MMPBSACalculation


                if sysid not in self.systems:
                    self.systems[sysid] = CalculationSystem(sysid)
                else:
                    raise ValueError(f'This system is already loaded.')

                if method in self.systems[sysid].methods:
                    raise ValueError(f'This system already contain results for {method}.')

                info = pickle.load(bf)
                # print(f"{info = }")
                bdata = pickle.load(bf)
                self.systems[sysid].methods[method] = MethodClass(
                    sys_name=sys_name or f'S-{method.upper()}-{sysid[:7]}',
                    app_namespace=info,
                    data= {'energy_normal': bdata.normal, 'energy_mutant': bdata.mutant,
                           'energy_mutant-normal': bdata.mut_norm,
                           'decomp_normal': bdata.decomp_normal, 'decomp_mutant': bdata.decomp_mutant}
                                                                  )


            # print(pd.DataFrame(flatten(_oringin)))
            # print(_oringin)
        # temp = Path(file)
        # if temp.is_file():
        #     pass

        return



class CalculationSystems:
    def __init__(self):
        super().__init__()
        self.systems = {}

    def __setitem__(self, key, value):
        self.systems[key] = value

    def __getitem__(self, item):
        if item in self.systems:
            return self.systems[item]
        elif isinstance(item, int):
            return self.systems[list(self.systems.keys())[item]]
        else:
            raise IndexError(f'{item} is not contained either as key or index...')

    def __repr__(self):
        return self.systems

    def __str__(self):
        return f"CalculationSystems = {self.systems}"


class CalculationSystem:
    def __init__(self, id):
        self.sysid = id
        self.methods = {}

    def __getitem__(self, item):
        return self.methods[item]

    def __repr__(self):
        return f"CalculationSystem: {self.methods}"
    #
    # def __str__(self):
    #     return "CalculationSystem"

    def get_calculation_method(self, method=None):
        pass



api = xBFreEAPI()
api.load_files('/home/mario/Documents/xBFreE_test/1.x.x/examples/gmx_example/COMPACT_RESULTS_MMPBSA.xbfree')
print(api.systems)
print(api.systems[0]['mmpbsa']['enthalpy'][:, ['gb', 'gbnsr6'], 'delta'])




































# Not implemented
class LIESystem:
    def __init__(self):
        pass

import pickle
from pathlib import Path
from typing import Union

import pandas as pd


def flatten(dictionary, parent_key: list = False):
    """
    Turn a nested dictionary into a flattened dictionary
    :param dictionary: The dictionary to flatten
    :param parent_key:The accumulated list of keys
    :return: A flattened dictionary with key as tuples of nested keys
    """

    items = []
    for key, value in dictionary.items():
        new_key = parent_key + [key] if parent_key else [key]
        if isinstance(value, dict):
            items.extend(flatten(value, new_key).items())
        else:
            items.append((tuple(new_key), value))
    return dict(items)


def load_file(file: Union[list[str, Path], list[str], list[Path], str, Path]):
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

    with open(file, 'rb') as bf:
        sysinfo = pickle.load(bf)
        info = pickle.load(bf)
        print(f"{info = }")
        bdata = pickle.load(bf)
        _oringin = {'normal': bdata.normal, 'mutant': bdata.mutant, 'decomp_normal': bdata.decomp_normal,
                         'decomp_mutant': bdata.decomp_mutant, 'mutant-normal': bdata.mut_norm}

        print(pd.DataFrame(flatten(_oringin)))
        print(_oringin)
    # temp = Path(file)
    # if temp.is_file():
    #     pass


    return


def split_data(d):
    data = {
        'energy': {
            'normal': {},
            'mutant': {},
            'mutant-normal': {}
        },
        'decomposition_energy': {}
    }

    if d.normal:
        for k, v in d.items():
            if k not in ['nmode', 'ie', 'c2', 'qh']:




load_file('/home/mario/Documents/xBFreE_test/1.x.x/examples/gmx_example/COMPACT_RESULTS_MMPBSA.xbfree')
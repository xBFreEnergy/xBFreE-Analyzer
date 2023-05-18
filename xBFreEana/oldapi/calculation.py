import logging
import math
import numpy as np
import pandas as pd
from tqdm import tqdm

import parmed
from typing import Union

TQDM_BAR_FORMAT = '            {l_bar}{bar}| {n_fmt}/{total_fmt} [elapsed: {elapsed} remaining: {remaining}]'
sep = '-------------------------------------------------------------------------------'

class Residue(object):
    def __init__(self, index, number, chain, mol_id, id_index, name, icode=''):
        self.index = int(index)
        self.number = number
        self.chain = chain
        self.mol_id = mol_id
        self.id_index = id_index
        self.name = name
        self.icode = icode
        self.mutant_label = None
        self.string = f"{mol_id}:{chain}:{name}:{number}:{icode}" if icode else f"{mol_id}:{chain}:{name}:{number}"
        self.mutant_string = None

    def __repr__(self):
        text = f"{type(self).__name__}(index: {self.index}, {self.mol_id}:{self.chain}:{self.name}:{self.number}"
        if self.icode:
            text += f":{self.icode}"
        text += ')'
        return text

    def __str__(self):
        return f"{self.index}"

    def __add__(self, other):
        if isinstance(other, Residue):
            return int(self.index + other.index)
        return int(self.index + other)

    def __sub__(self, other):
        if isinstance(other, Residue):
            return int(self.index - other.index)
        return int(self.index - other)

    def __int__(self):
        return self.index

    def is_mutant(self):
        return bool(self.mutant_label)

    def is_receptor(self):
        return self.mol_id == 'R'

    def is_ligand(self):
        return self.mol_id == 'L'

    def issame(self, other):
        pass

    def set_mut(self, mut):
        self.mutant_label = f'{self.chain}/{self.number}{f":{self.icode}" if self.icode else ""} - {self.name}x{mut}'
        self.mutant_string = (f"{self.mol_id}:{self.chain}:{mut}:{self.number}:{self.icode}" if self.icode
                              else f"{self.mol_id}:{self.chain}:{mut}:{self.number}")


def mask2list(com_str, rec_mask, lig_mask):
    rm_list = rec_mask.strip(":").split(',')
    lm_list = lig_mask.strip(':').split(',')
    res_list = []

    for r in rm_list:
        if '-' in r:
            s, e = r.split('-')
            res_list.extend([i, 'R'] for i in range(int(s) - 1, int(e)))
        else:
            res_list.append([int(r) - 1, 'R'])
    for l in lm_list:
        if '-' in l:
            s, e = l.split('-')
            res_list.extend([i, 'L'] for i in range(int(s) - 1, int(e)))
        else:
            res_list.append([int(l) - 1, 'L'])
    res_list = sorted(res_list, key=lambda x: x[0])
    comstr = parmed.load_file(com_str)
    resl = []
    rec_index = 1
    lig_index = 1
    for res, rl in zip(comstr.residues, res_list):
        if rl[1] == 'R':
            resl.append(Residue(rl[0] + 1, res.number, res.chain, rl[1], rec_index, res.name, res.insertion_code))
            rec_index += 1
        else:
            resl.append(Residue(rl[0] + 1, res.number, res.chain, rl[1], lig_index, res.name, res.insertion_code))
            lig_index += 1
    return resl


class InteractionEntropyCalc:
    """
    Class for Interaction Entropy calculation
    :return {IE_key: data}
    """

    def __init__(self, ggas, INPUT, method, iesegment=None):
        """

        Args:
            ggas: Model GGAS energy
            INPUT: INPUT dict
            iesegment: If not defined, iesegment = INPUT['ie_segment']
        """
        self.ggas = ggas
        self.INPUT = INPUT
        self.method = method
        self.isegment = iesegment or INPUT['general']['ie_segment']
        self.data = []

        self._calculate()

    def _calculate(self):
        # boltzmann constant in kcal/(mol⋅K)
        k = 0.001985875
        temperature = self.INPUT['general']['temperature']

        exp_energy_int = np.array([], dtype=float)
        self.data = np.zeros(self.ggas.size, dtype=float)

        for i in tqdm(range(self.ggas.size), bar_format=TQDM_BAR_FORMAT, ascii=True):
            aeint = self.ggas[:i + 1].mean()
            deint = self.ggas[i] - aeint
            try:
                eceint = math.exp(deint / (k * temperature))
            except Exception:
                logging.warning('The internal energy of your system has very large energy fluctuation so it is not '
                                'possible to continue with the calculations. Please, make sure your system is '
                                'consistent')
                logging.info('The Interaction Entropy will be skipped...')
                self.INPUT['general']['interaction_entropy'] = 0
                break
            exp_energy_int = np.append(exp_energy_int, eceint)
            aeceint = exp_energy_int.mean()
            cts = k * temperature * math.log(aeceint)
            self.data[i] = cts

        numframes = len(self.data)
        self.ie_std = float(self.ggas.std())
        self.ieframes = math.ceil(numframes * (self.isegment / 100))
        self.iedata = self.data[-self.ieframes:]

    def save_output(self, filename):
        frames = list(
            range(
                self.INPUT['general']['startframe'],
                self.INPUT['general']['startframe'] + len(self.data) * self.INPUT['general']['interval'],
                self.INPUT['general']['interval'],
            )
        )
        with open(filename, 'w') as out:
            out.write(f'| Interaction Entropy results for {self.method} calculations\n')
            out.write(f'IE-frames: last {self.ieframes}\n')
            out.write(f'Internal Energy SD (sigma): {self.ie_std:9.2f}\n')
            out.write(f'| Interaction Entropy (-TΔS): {self.iedata.mean():9.2f} +/- {self.iedata.std():7.2f}\n\n')
            out.write('| Interaction Entropy per-frame:\n')

            out.write('Frame # | IE value\n')
            for f, d in zip(frames, self.data):
                out.write('{:d}  {:.2f}\n'.format(f, d))


class C2EntropyCalc:
    """
    Class for Interaction Entropy calculation
    :return {IE_key: data}
    """

    def __init__(self, ggas, INPUT, method):
        self.ggas = ggas
        self.INPUT = INPUT
        self.method = method

        self._calculate()

    def _calculate(self):
        # gas constant in kcal/(mol⋅K)
        R = 0.001987
        temperature = self.INPUT['general']['temperature']
        self.ie_std = float(self.ggas.std())
        self.c2data = (self.ie_std ** 2) / (2 * temperature * R)

        size = self.ggas.size
        array_of_c2 = np.zeros(2000)
        for i in range(2000):
            idxs = np.random.randint(0, size, size)
            ie_std = self.ggas[idxs].std()
            c2data = (ie_std ** 2) / (2 * temperature * R)
            array_of_c2[i] = c2data

        self.c2_std = float(np.sort(array_of_c2)[100:1900].std())
        self.c2_ci = np.percentile(np.sort(array_of_c2)[100:1900], [2.5, 97.5])

    def save_output(self, filename):
        with open(filename, 'w') as out:
            out.write(f'| C2 Entropy results for {self.method} calculations\n')
            out.write(f'C2 Entropy (-TΔS): {self.c2data:.4f}\n')
            out.write(f'C2 Entropy SD: {self.c2_std:.4f}\n')
            out.write(f'Internal Energy SD (sigma): {self.ie_std:9.2f}\n')
            out.write(f'C2 Entropy CI: {self.c2_ci[0]:.4f} {self.c2_ci[1]:.4f}\n')


class IEout(dict):
    """
    Interaction Entropy output
    """

    def __init__(self, INPUT, method, **kwargs):
        super(IEout, self).__init__(**kwargs)
        self.INPUT = INPUT
        self.method = method

    def parse_from_dict(self, d: dict):
        self.update(d)

    def parse_from_file(self, filename, numframes=1):
        self['data'] = EnergyVector(numframes)
        with open(filename) as of:
            c = 0
            f = 0
            while line := of.readline():
                f += 1
                if line.startswith('|') or not line.split():
                    continue
                if line.startswith('IE-frames:'):
                    self['ieframes'] = int(line.strip('\n').split()[-1])
                elif line.startswith('Internal Energy SD (sigma):'):
                    self['sigma'] = float(line.strip('\n').split()[-1])
                elif line.startswith('Frame'):
                    continue
                else:
                    frame, value = line.strip('\n').split()
                    self['data'][c] = float(value)
                    c += 1
                f += 1
        self['iedata'] = self['data'][-self['ieframes']:]

    def _print_vectors(self, csvwriter):
        """ Prints the energy vectors to a CSV file for easy viewing
            in spreadsheets
        """
        csvwriter.writerow(['Frame #', 'Interaction Entropy'])
        f = self.INPUT['general']['startframe']
        for d in self['data']:
            csvwriter.writerow([f] + [round(d, 2)])
            f += self.INPUT['general']['interval']
        csvwriter.writerow([])

    def summary_output(self):
        summary = self.summary()
        text = []
        for row in summary:
            met, key, sigma, avg, std, sem = row
            if isinstance(avg, str):
                text.extend((
                    f'{met:16s} {key:>13s} {sigma:>13s} {avg:>10s} {std:>12s} {sem:>10s}',
                    sep,
                ))
            else:
                text.append(f'{met:16s} {key:>13s} {sigma:13.2f} {avg:10.2f} {std:12.2f} {sem:10.2f}')
        return '\n'.join(text) + '\n\n'

    def summary(self):
        """ Formatted summary of Interaction Entropy results """

        avg = float(self['data'][-self['ieframes']:].mean())
        stdev = float(self['data'][-self['ieframes']:].stdev())
        sem = float(self['data'][-self['ieframes']:].sem())

        return [
            [
                'Energy Method',
                'Entropy',
                'σ(Int. Energy)',
                'Average',
                'SD',
                'SEM'
            ],
            [self.method.upper(), 'IE', self['sigma'], avg, stdev, sem]
        ]


class C2out(dict):
    """
    C2 Entropy output
    """

    def __init__(self, method, **kwargs):
        super(C2out, self).__init__(**kwargs)
        self.method = method

    def parse_from_dict(self, d):
        self.update(d)

    def parse_from_file(self, filename):
        with open(filename) as of:
            while line := of.readline():
                if line.startswith('|') or not line:
                    continue
                if line.startswith('C2 Entropy (-TΔS):'):
                    self['c2data'] = float(line.strip('\n').split()[-1])
                elif line.startswith('C2 Entropy SD:'):
                    self['c2_std'] = float(line.strip('\n').split()[-1])
                elif line.startswith('Internal Energy SD (sigma):'):
                    self['sigma'] = float(line.strip('\n').split()[-1])
                elif line.startswith('C2 Entropy CI:'):
                    self['c2_ci'] = [float(line.strip('\n').split()[-2]), float(line.strip('\n').split()[-1])]

    def summary_output(self):
        summary = self.summary()
        text = []
        for row in summary:
            met, key, sigma, avg, std, ci = row
            if isinstance(avg, str):
                text.extend((f'{met:16s} {key:>13s} {sigma:>13s} {avg:>10s} {std:>8s} {ci:>14s}', sep))
            else:
                text.append(f"{met:16s} {key:>13s} {sigma:13.2f} {avg:10.2f} {std:8.2f} {ci:>14s}")
        return '\n'.join(text) + '\n\n'

    def summary(self):
        """ Formatted summary of C2 Entropy results """

        return [
            [
                'Energy Method',
                'Entropy',
                'σ(Int. Energy)',
                'C2 Value',
                'SD',
                'C.Inter.(95%)'
            ],
            [self.method.upper(), 'C2', float(self['sigma']), float(self['c2data']), float(self['c2_std']),
             f"{self['c2_ci'][0]:.2f}-{self['c2_ci'][1]:.2f}",]
        ]


class EnergyVector(np.ndarray):
    def __new__(cls, values=None, com_std=None):
        # Input array is an already formed ndarray instance
        # We first cast to be our class type
        if isinstance(values, int):
            obj = np.zeros((values,)).view(cls)
        elif isinstance(values, (list, tuple, np.ndarray)):
            obj = np.array(values).view(cls)
        else:
            obj = np.array([]).view(cls)
        obj.com_std = com_std
        return obj

    def __array_finalize__(self, obj):
        # see InfoArray.__array_finalize__ for comments
        if obj is None:
            return
        self.com_std = getattr(obj, 'com_std', None)

    # This fix the pickle problem. Taken from
    # https://stackoverflow.com/questions/26598109/preserve-custom-attributes-when-pickling-subclass-of-numpy-array
    def __reduce__(self):
        # Get the parent's __reduce__ tuple
        pickled_state = super(EnergyVector, self).__reduce__()
        # Create our own tuple to pass to __setstate__
        new_state = pickled_state[2] + (self.__dict__,)
        # Return a tuple that replaces the parent's __setstate__ tuple with our own
        return (pickled_state[0], pickled_state[1], new_state)

    def __setstate__(self, state):
        self.__dict__.update(state[-1])  # Update the internal dict from state
        # Call the parent's __setstate__ with the other tuple elements.
        super(EnergyVector, self).__setstate__(state[:-1])

    def stdev(self):
        return self.com_std or self.std()

    def sem(self):
        return float(self.std() / math.sqrt(len(self)))

    def semp(self):
        return float(self.stdev() / math.sqrt(len(self)))

    def append(self, values):
        return EnergyVector(np.append(self, values))

    def avg(self):
        return np.average(self)

    def corr_add(self, other):
        selfstd = self.com_std or float(self.std())
        comp_std = None
        if isinstance(other, EnergyVector):
            otherstd = other.com_std or float(other.std())
            comp_std = get_corrstd(selfstd, otherstd)
        return EnergyVector(np.add(self, other), comp_std)

    def corr_sub(self, other):
        self_std = self.com_std or float(np.asarray(self).std())
        comp_std = None
        if isinstance(other, EnergyVector):
            other_std = other.com_std or float(np.asarray(other).std())
            comp_std = get_corrstd(self_std, other_std)
        return EnergyVector(np.subtract(self, other), comp_std)

    def __add__(self, other):
        selfstd = self.com_std or float(self.std())
        comp_std = None
        if isinstance(other, EnergyVector):
            otherstd = other.com_std or float(other.std())
            comp_std = get_std(selfstd, otherstd)
        return EnergyVector(np.add(self, other), comp_std)

    def __sub__(self, other):
        self_std = self.com_std or float(np.asarray(self).std())
        comp_std = None
        if isinstance(other, EnergyVector):
            other_std = other.com_std or float(np.asarray(other).std())
            comp_std = get_std(self_std, other_std)
        return EnergyVector(np.subtract(self, other), comp_std)

    def __eq__(self, other):
        return np.all(np.equal(self, other))

    def __lt__(self, other):
        return np.all(np.less(self, other))

    def __le__(self, other):
        return np.all(np.less_equal(self, other))

    def __gt__(self, other):
        return np.all(np.greater(self, other))

    def __ge__(self, other):
        return np.all(np.greater_equal(self, other))

    def abs_gt(self, val):
        """ If any element's absolute value is greater than a # """
        return np.any(np.greater(np.abs(self), val))

def get_std(val1, val2):
    return math.sqrt(val1 ** 2 + val2 ** 2)


def get_corrstd(val1, val2):
    return math.sqrt(val1 ** 2 + val2 ** 2 - 2 * val1 * val2)


def calc_sum(vector1, vector2, mut=False) -> (float, float):
    """
    Calculate the mean and std of the two vector/numbers sum
    Args:
        vector1: EnergyVector or float
        vector2: EnergyVector or float
        mut: If mutant, the SD is the standard deviation of the array

    Returns:
        dmean: Mean of the sum
        dstd: Standard deviation
    """
    if isinstance(vector2, EnergyVector) and isinstance(vector1, EnergyVector):
        if mut:
            d = vector2 + vector1
            dmean = float(d.mean())
            dstd = float(d.std())
        else:
            dmean = float(vector2.mean() + vector1.mean())
            dstd = float(get_std(vector2.std(), vector1.std()))
    elif isinstance(vector2, EnergyVector) and isinstance(vector1, (int, float)):
        dmean = float(vector2.mean() + vector1)
        dstd = vector2.std()
    elif isinstance(vector2, (int, float)) and isinstance(vector1, EnergyVector):
        dmean = float(vector2 + vector1.mean())
        dstd = vector1.std()
    else:
        dmean = float(vector2 + vector1)
        dstd = 0.0
    return dmean, dstd


def multiindex2dict(p: Union[pd.MultiIndex, pd.Index, dict]) -> dict:
    """
    Converts a pandas Multiindex to a nested dict
    :parm p: As this is a recursive function, initially p is a pd.MultiIndex, but after the first iteration it takes
    the internal_dict value, so it becomes to a dictionary
    """
    internal_dict = {}
    end = False
    for x in p:
        # Since multi-indexes have a descending hierarchical structure, it is convenient to start from the last
        # element of each tuple. That is, we start by generating the lower level to the upper one. See the example
        if isinstance(p, pd.MultiIndex):
            # This checks if the tuple x without the last element has len = 1. If so, the unique value of the
            # remaining tuple works as key in the new dict, otherwise the remaining tuple is used. Only for 2 levels
            # pd.MultiIndex
            if len(x[:-1]) == 1:
                t = x[:-1][0]
                end = True
            else:
                t = x[:-1]
            if t not in internal_dict:
                internal_dict[t] = [x[-1]]
            else:
                internal_dict[t].append(x[-1])
        elif isinstance(x, tuple):
            # This checks if the tuple x without the last element has len = 1. If so, the unique value of the
            # remaining tuple works as key in the new dict, otherwise the remaining tuple is used
            if len(x[:-1]) == 1:
                t = x[:-1][0]
                end = True
            else:
                t = x[:-1]
            if t not in internal_dict:
                internal_dict[t] = {x[-1]: p[x]}
            else:
                internal_dict[t][x[-1]] = p[x]
    if end:
        return internal_dict
    return multiindex2dict(internal_dict)


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


def emapping(d):
    internal_dict = {}
    for k, v in d.items():
        if isinstance(v, dict):
            if v.values():
                if isinstance(list(v.values())[0], (dict, pd.DataFrame)):
                    internal_dict[k] = emapping(v)
                else:
                    internal_dict[k] = list(v.keys())
        elif isinstance(v, pd.DataFrame):
            internal_dict[k] = multiindex2dict(v.columns)
        else:
            internal_dict[k] = v
    return internal_dict

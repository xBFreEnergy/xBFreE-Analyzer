import warnings
from .utils import arg2tuple
import pandas as pd


def _get_frames(self):
    ts = timestep or 1

    INPUT = app_namespace.INPUT
    numframes = app_namespace.INFO['numframes']
    nmnumframes = app_namespace.INFO['numframes_nmode']

    frames_list = list(range(INPUT['general']['startframe'],
                             INPUT['general']['startframe'] + numframes * INPUT['general']['interval'],
                             INPUT['general']['interval']))
    frames_list = frames_list
    INPUT['general']['endframe'] = frames_list[-1]
    time_step_list = list(range(starttime,
                                starttime + len(frames_list) * ts * INPUT['general']['interval'],
                                ts * INPUT['general']['interval']))
    frames = dict(zip(frames_list, time_step_list))

    if INPUT['nmode']['nmoderun']:
        nmframes_list = list(range(INPUT['nmode']['nmstartframe'],
                                   INPUT['nmode']['nmstartframe'] + nmnumframes * INPUT['nmode']['nminterval'],
                                   INPUT['nmode']['nminterval']))
        INPUT['nmode']['nmendframe'] = nmframes_list[-1]

        nm_start = (nmframes_list[0] - frames_list[0]) * INPUT['general']['interval']
        nmtime_step_list = list(range(starttime + nm_start,
                                      starttime + nm_start + len(nmframes_list) * ts * INPUT['nmode'][
                                          'nminterval'],
                                      ts * INPUT['nmode']['nminterval']))
        nmframes_list = nmframes_list
        nmframes = dict(zip(nmframes_list, nmtime_step_list))

def _get_frames_index(framestype, startframe, endframe, interval):
    if framestype == 'energy':
        start = list(frames.keys()).index(startframe) if startframe else startframe
        end = list(frames.keys()).index(endframe) + 1 if endframe else endframe
        index_frames = {f: frames[f] for f in list(frames.keys())[start:end:interval]}
    else:
        start = list(nmframes.keys()).index(startframe) if startframe else startframe
        end = list(nmframes.keys()).index(endframe) + 1 if endframe else endframe
        index_frames = {f: nmframes[f] for f in list(nmframes.keys())[start:end:interval]}
    return (start, end, pd.Series(index_frames.values(), name=f'Time ({timeunit})') if timestep
    else pd.Series(index_frames.keys(), name='Frames'))


def get_energy(etype: tuple = None, model: tuple = None, mol: tuple = None, term: tuple = None,
               remove_empty_terms=True, threshold=0.01, startframe=None, endframe=None, interval=1, verbose=True):
    """
    Get energy
    Args:
        keys: Energy levels

    Returns: Energy pd.Dataframe

    """
    # get start and end for frames range
    if etype:
        etype = arg2tuple(etype)
    if model:
        model = arg2tuple(model)
    if mol:
        mol = arg2tuple(mol)
    if term:
        term = arg2tuple(term)
    s, e, index = _get_frames_index('energy', startframe, endframe, interval)
    e_map = {}
    energy = {}
    summ_df = {}
    comp_summary = {}
    temp_print_keys = etype or tuple(x for x in ['normal', 'mutant', 'mutant-normal'] if x in data)

    for et in temp_print_keys:
        if et not in data:
            if verbose:
                warnings.warn(f'Not etype {et} in data')
        elif not data[et]:
            continue
        else:
            e_map[et] = {}
            energy[et] = {}
            summ_df[et] = {}
            comp_summary[et] = {}
            temp_model_keys = model or tuple(x for x in data[et].keys() if x not in ['nmode', 'qh', 'ie' ,'c2'])

            for m in temp_model_keys:
                if m in data[et]:
                    e_map[et][m] = {}
                    model_energy = {}
                    temp_mol_keys = mol or tuple(data[et][m].keys())

                    for m1 in temp_mol_keys:
                        if m1 in data[et][m]:
                            e_map[et][m][m1] = []
                            model_energy[m1] = {}
                            temp_terms_keys = ([x for x in data[et][m][m1].keys() if x in term] if term
                                               else tuple(data[et][m][m1].keys()))
                            valid_terms = []

                            for t in temp_terms_keys:
                                if t not in data[et][m][m1]:
                                    if verbose:
                                        warnings.warn(f'Not term {t} in etype {et} > model {m} > mol {m1}')
                                elif (
                                        not remove_empty_terms
                                        or abs(data[et][m][m1][t].mean())
                                        >= threshold or t in ['GSOLV', 'GGAS', 'TOTAL']
                                ):
                                    e_map[et][m][m1].append(t)
                                    model_energy[m1][t] = data[et][m][m1][t][s:e:interval]
                                    valid_terms.append(t)
                        elif verbose:
                            warnings.warn(f'Not mol {m1} in etype {et} > model {m}')
                    energy[et][m], summ_df[et][m] = _model2df(model_energy, index)

                elif verbose:
                    warnings.warn(f'Not model {m} in etype {et}')
    corr = {}
    for et, v in summ_df.items():
        corr[et] = {}
        for m, v2 in v.items():
            if 'delta' in v2:
                corr[et][m] = pd.DataFrame(
                    {('ΔGeff', t): v for t, v in v2['delta']['TOTAL'].to_dict().items()}, index=[0])
    return {'map': e_map, 'data': energy, 'summary': summ_df, 'correlation': corr}
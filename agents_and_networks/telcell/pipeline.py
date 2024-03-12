from typing import Any, Iterable, Mapping, Tuple, List

from tqdm import tqdm

from telcell.utils.transform import is_colocated
from telcell.data.models import Track
from telcell.models import Model


def run_pipeline(
        data: Iterable[Tuple[Track, Track, Mapping[str, Any]]],
        model: Model,
        **kwargs
) -> Tuple[List[float], List[bool], List[Mapping[str, Any]]]:

    lrs = []
    y_true = []
    extras = []
    for track_a, track_b, data_kwargs in tqdm(data, 'Running pipeline for each track pair in data'):
        lr, extra = model.predict_lr(track_a, track_b, **data_kwargs, **kwargs)
        # it's possible we could not provide an lr, in that case return None
        # (as other methods may be able to handle this day)
        lrs.append(lr)
        y_true.append(is_colocated(track_a, track_b))
        extras.append(extra)
    return lrs, y_true, extras

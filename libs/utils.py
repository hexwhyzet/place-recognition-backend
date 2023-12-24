import random
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from uuid import uuid4

import numpy as np
from tqdm import tqdm

from resources.extra.adjectives import adjectives_list
from resources.extra.philosophers import philosophers_list


def camel_to_snake(camel_text):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', camel_text).lower()


def rle_encode(array):
    res = []

    ctr = 1
    for i in range(1, len(array)):
        if array[i] != array[i - 1]:
            res.append((ctr, array[i - 1]))
            ctr = 1
        else:
            ctr += 1
    res.append((ctr, array[-1]))
    return res


def rle2mask(rle, shape):
    '''
    mask_rle: run-length as string formated (start length)
    shape: (width,height) of array to return
    Returns numpy array, 1 - mask, 0 - background
    '''
    cur = 0
    img = np.zeros(shape[0] * shape[1], dtype=np.bool_)
    for idx, sector in enumerate(rle):
        img[cur:cur + sector] = idx % 2
        cur += sector
    return img.reshape(shape).T


def generate_release_name():
    return random.choice(adjectives_list).lower() + "_" + random.choice(philosophers_list).lower()


def generate_int_uuid(bits: int = 128) -> int:
    assert bits <= 128
    return uuid4().int >> (128 - bits)


def generate_int_uuid64() -> int:
    return generate_int_uuid(64)


def generate_hex_uuid() -> str:
    return uuid4().hex


def pbar_wrapper(pbar, func, *args, **kwargs):
    result = func(*args, **kwargs)
    pbar.update(1)
    return result


def pool_executor(items, processor_fn, processor_args, processor_kwargs, tqdm_desc, max_workers):
    with tqdm(total=len(items), desc=tqdm_desc) as pbar:
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            futures = [pool.submit(pbar_wrapper, pbar, processor_fn, item, *processor_args, **processor_kwargs) for item in items]
            results = [future.result() for future in as_completed(futures)]
            return results


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]

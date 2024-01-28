import os
import random
import re
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
import time
from typing import List, Callable
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


class Delayed:
    def __init__(self, func: Callable, delay: float):
        self.func = func
        self.delay = delay

    def __call__(self, *args, **kwargs):
        if self.delay:
            time.sleep(self.delay)
        return self.func(*args, **kwargs)


def pool_executor(items, processor_fn: Callable, max_workers: int, executor_type: str, processor_args: List = None,
                  processor_kwargs: dict = None, tqdm_desc: str = None, delay: float = 0):
    if executor_type not in ["process", "thread"]:
        raise Exception(f"Wrong executor type: '{executor_type}'")

    if processor_args is None:
        processor_args = list()

    if processor_kwargs is None:
        processor_kwargs = dict()

    if tqdm_desc is None:
        tqdm_desc = "Default description"

    executor = ProcessPoolExecutor if executor_type == "process" else ThreadPoolExecutor

    with tqdm(total=len(items), desc=tqdm_desc) as pbar:
        with executor(max_workers=max_workers) as pool:
            futures = []

            for item in items:
                future = pool.submit(Delayed(processor_fn, delay), item, *processor_args, **processor_kwargs)
                future.add_done_callback(lambda p: pbar.update())
                futures.append(future)

            results = []
            for future in futures:
                result = future.result()
                results.append(result)
            return results


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def path_join(path, *parts):
    return os.path.join(path, *parts).replace('\\', '/')  # Windows workaround

# Partially based on https://github.com/openai/gym under the following license:
#
# The MIT License
#
# Copyright (c) 2016 OpenAI (http://openai.com)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import hashlib
import numbers
import os
import random
import struct
import numpy      as np
import tensorflow as tf


SEEDED  = False
seeder  = np.random.RandomState()


def set_random_seeds(seed):
  global SEEDED
  if seed < 0 or SEEDED:
    return
  SEEDED = True

  # Set the RLTF seed
  seeder.seed(seed)

  # Sample separate seeds from seeder to avoid correlation among modules
  # NOTE: For the same seed, the sampled sequence of module seeds will always be the same
  tf.set_random_seed(hash_seed(create_seed()))
  np.random.seed(hash_seed(create_seed()))
  random.seed(hash_seed(create_seed()))


def get_prng(seed=None):
  """Creates a new instance of a pseudo-random number generator (prng). If `SEEDED==True` (seed has
  been set globally), then the prng is also seeded deterministically. Otherwise, it is seeded with a
  random seed. If `seed=None` and `SEEDED==True`, `seed` will be autogenerated in a deterministic way
  by a custom prng, provided that the order of calls to this subroutine remains the same between
  different runs of your program.
  Args:
    seed: int or None. If int, the prng will be seeded with this number. Otherwise, a seed will be
      automatically generated
  Returns:
    np.random.RandomState: the pseudo-random number generator
  """
  if seed is not None and not (isinstance(seed, numbers.Integral) and seed >= 0):
    raise ValueError('Seed must be a non-negative integer or omitted, not {}'.format(seed))

  prng = np.random.RandomState()
  seed = create_seed(seed)
  seed = _int_list_from_bigint(hash_seed(seed))
  prng.seed(seed)
  return prng


def create_seed(seed=None, max_bytes=4):
  if seed is not None:
    seed = seed % 2**(8 * max_bytes)
  else:
    if SEEDED:
      seed = seeder.randint(0, 2**(8*max_bytes))
    else:
      seed = _bigint_from_bytes(os.urandom(max_bytes))
  return seed


def hash_seed(seed=None, max_bytes=4):
  """Different modules are likely to request an autogenerated seed. There is literature
  indicating that generating seeds in a linear fashion will cause correlated outputs
  generated by those seeds. To avoid this, we need to generate the seeds in a non-linear
  fashion. For more details check:

  http://blogs.unity3d.com/2015/01/07/a-primer-on-repeatable-random-numbers/
  http://stackoverflow.com/questions/1554958/how-different-do-random-seeds-need-to-be
  http://dl.acm.org/citation.cfm?id=1276928

  Thus, we hash the seeds, which should get rid of simple correlations.

  Args:
    seed: int
    max_bytes: Maximum number of bytes to use in the hashed seed.
  Returns:
    int - the hashed seed
  """
  hash_code = hashlib.sha512(str(seed).encode('utf8')).digest()
  return _bigint_from_bytes(hash_code[:max_bytes])


def _bigint_from_bytes(data):
  sizeof_int = 4
  padding = sizeof_int - len(data) % sizeof_int
  data += b'\0' * padding
  int_count = int(len(data) / sizeof_int)
  unpacked = struct.unpack("{}I".format(int_count), data)
  accum = 0
  for i, val in enumerate(unpacked):
    accum += 2 ** (sizeof_int * 8 * i) * val
  return accum


def _int_list_from_bigint(bigint):
  # Special case 0
  if bigint < 0:
    raise ValueError('Seed must be non-negative, not {}'.format(bigint))
  elif bigint == 0:
    return [0]

  ints = []
  while bigint > 0:
    bigint, mod = divmod(bigint, 2 ** 32)
    ints.append(mod)
  return ints


# def get_prng(seed=None):
#   """Creates a new instance of a pseudo-random number generator (prng). If `SEEDED==True` (seed has
#   been set globally), then the prng is also seeded deterministically. Otherwise, it is seeded with a
#   random seed. If `seed=None` and `SEEDED==True`, `seed` will be autogenerated in a deterministic way
#   by a custom prng, provided that the order of calls to this subroutine remains the same between
#   different runs of your program.
#   Args:
#     seed: int or None. If int, the prng will be seeded with this number. Otherwise, a seed will be
#       automatically generated
#   Returns:
#     np.random.RandomState: the pseudo-random number generator
#   """
#   from gym.utils import seeding
#   max_bytes = 8
#   if SEEDED and seed is not None:
#     seed = seeder.randint(0, 2**(8*max_bytes))
#   prng, seed = seeding.np_random(seed)
#   return prng

#! /usr/bin/env python

# Downselect phasing data we received from David Kaplan
# First I converted the .ms files to uvfits using casa's exportuvfits task

import pyuvdata
import numpy as np

uv = pyuvdata.UVData()
# First file phased to 01h39m00.0s -17d57m00s
print('Reading first file')
uv.read_uvfits('pyuvdata/data/1133866760.uvfits')

unique_times = np.unique(uv.time_array)
uv.select(freq_chans=[217, 218], times=unique_times[[2, uv.Ntimes / 2]],
          polarizations=[-5], ant_pairs_nums=(90, 127))

print('Writing first file')
uv.write_uvfits('pyuvdata/data/1133866760_1.uvfits')

# Second file phased to 00h00m00.0s -18d00m00s
print('Reading second file')
uv.read_uvfits('pyuvdata/data/1133866760_rephase.uvfits')

unique_times = np.unique(uv.time_array)
uv.select(freq_chans=[217, 218], times=unique_times[[2, uv.Ntimes / 2]],
          polarizations=[-5], ant_pairs_nums=(90, 127))

print('Writing second file')
uv.write_uvfits('pyuvdata/data/1133866760_2.uvfits')

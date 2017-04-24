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
uv.select(freq_chans=[0, 1], times=unique_times[[0, uv.Ntimes / 2]],
          polarizations=[-5], ant_pairs_nums=(2, 11))

print('Writing first file')
uv.write_uvfits('pyuvdata/data/1133866760_downselect.uvfits')

# Second file phased to 00h00m00.0s -18d00m00s
print('Reading second file')
uv.read_uvfits('pyuvdata/data/1133866760.uvfits')

unique_times = np.unique(uv.time_array)
uv.select(freq_chans=[0, 1], times=unique_times[[0, uv.Ntimes / 2]],
          polarizations=[-5], ant_pairs_nums=(2, 11))

print('Writing second file')
uv.write_uvfits('pyuvdata/data/1133866760_rephase_downselect.uvfits')

"""
Tests for mmode transfer matrix translation
"""

import nose.tools as nt
import os
from pyuvdata import UVData
import pyuvdata.utils as uvutils
import pyuvdata.tests as uvtest
from pyuvdata.data import DATA_PATH
import numpy as np
from pyuvdata.mmode import BeamTransferer
from pyuvsim import AnalyticBeam
testdir = os.path.join(DATA_PATH, 'test/')


def test_write_transfer_matrices():
    '''
    test computing a transit telescope
    from analytic beam simulation
    and writing transfer matrix
    '''
    uv_uniform = UVData()
    uv_uniform.read_uvfits(os.path.join(testdir,'two_antennas_equator_uniform.uvfits'))
    uv_beams_uniform = [ AnalyticBeam('uniform'), AnalyticBeam('uniform') ]
    outdir = os.path.join(testdir, 'mmode_out_uniform')
    uv_drift_uniform = BeamTransferer(uvdata = uv_uniform, uvbeams = uv_beams_uniform, directory = outdir)
    uv_drift_uniform.write_transfer()

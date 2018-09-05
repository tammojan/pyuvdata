'''
mmode is a wrapper for a UVbeam object and UVdata object with functions
to export uvdata objects to m-mode analysis beam-transfer matrices.

Functionality will hopefully eventually include importing m-mode data-sets
and reading/writing uvdata to m-mode time-streams.

requires the driftscan library to be installed
'''
import numpy as np
from caput import config
from caput import time as ctime
from uvdata import UVData
from uvbeam import UVBeam
from drift.core.telescope import SimplePolarisedTelescope
from pyuvsim import AnalyticBeam
from drift.core.beamtransfer import BeamTransfer
C = 299792458.
# Complete klooge! Telescope class needs to be redesigned so that
# the frequency channels are not class properties!
FREQ_LOW = 420.
FREQ_HIGH = 420.1
NUM_CHAN = 1
# speed of light
# create abstract telescope class


class UVPolarisedTelescope(SimplePolarisedTelescope):
    freq_lower = FREQ_LOW
    freq_upper = FREQ_HIGH
    num_freq = NUM_CHAN
    def __init__(self, uvdata, uvbeams, uv_res=0.5):
        self.uvdata = uvdata
        self.uvbeams = uvbeams
        self.uv_res = uv_res
        self.min_lambda = C / uvdata.freq_array.max()
        # make sure that all beams are in healpix format
        #self.freq_lower = uvdata.freq_array.min()/1e6
        #self.freq_upper = uvdata.freq_array.max()/1e6
        #self.num_freq = len(uvdata.freq_array)

    def beamx(self, feed, freq):
        """Beam for the X polarisation feed.

        Parameters
        ----------
        feed : integer
            Index for the feed.
        freq : integer
            Index for the frequency.

        Returns
        -------
        beam : np.ndarray
            Healpix maps (of size [self._nside, 2]) of the field pattern in the
            theta and phi directions.
        """
        fnum = int(np.mod(feed, len(self.uvbeams)))
        return self.uvbeams[fnum].interp(self._angpos[:, 1],
                                         self._angpos[:, 0],
                                         np.array([self.frequencies[freq]])*1e6)[0][:, 0, 0, 0, :].squeeze().T

    def beamy(self, feed, freq):
        """Beam for the Y polarisation feed.

        Parameters
        ----------
        feed : integer
            Index for the feed.
        freq : integer
            Index for the frequency.

        Returns
        -------
        beam : np.ndarray
            Healpix maps (of size [self._nside, 2]) of the field pattern in the
            theta and phi directions.
        """
        fnum = int(np.mod(feed, len(self.uvbeams)))
        return self.uvbeams[fnum].interp(self._angpos[:, 1],
                                         self._angpos[:, 0],
                                         np.array([self.frequencies[freq]])*1e6)[0][:, 0, 1, 0, :].squeeze().T
    # Set the feed array of feed positions (in metres EW, NS)

    @property
    def _single_feedpositions(self):
        # Do DriftScanTelescopes support 3d antenna positions?
        pos = self.uvdata.get_ENU_antpos(pick_data_ants=True)[0][:, :-1]
        return pos

    # Give the widths in the U and V directions in metres (used for
    # calculating the maximum l and m)
    @property
    def u_width(self):
        return self.uv_res * self.min_lambda

    @property
    def v_width(self):
        return self.uv_res * self.min_lambda


class BeamTransferer():
    def __init__(self, uvdata, uvbeams, directory='.', uv_res=0.5):
        FREQ_LOW = uvdata.freq_array.min()/1e6 # telescope class expects frequencies in MHz.
        FREQ_HIGH = uvdata.freq_array.max()/1e6 # telescope class expects frequencies in MHz.
        NUM_CHAN = len(uvdata.freq_array)
        my_telescope = UVPolarisedTelescope(uvdata=uvdata, uvbeams=uvbeams, uv_res=uv_res)
        self.beam_transfer = BeamTransfer(directory=directory, telescope=my_telescope)

    def write_transfer(self):
        '''
        Write transfer matrices
        '''
        self.beam_transfer.generate()

    def write_data(self):
        '''
        Write data into time-stream format.
        '''
        return

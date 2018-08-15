'''
mmode is a wrapper for a UVbeam object and UVdata object with functions
to export uvdata objects to m-mode analysis beam-transfer matrices.

Functionality will hopefully eventually include importing m-mode data-sets
and reading/writing uvdata to m-mode time-streams.

requires the driftscan library to be installed
'''

from caput import config
from caput import time as ctime
from uvdata import UVData
import uvbeam as UVBeam
from drift.core.telescope import SimplePolarisedTelescope
from pyuvsim import AnalyticBeam
from drift.core.beamtransfer import BeamTransfer

class UVDataDrift():
    """
    Class Defining a uvdata+uvbeam object for export to a DriftScanTelescope
    object used in m-mode analyses.
    https://github.com/radiocosmology/driftscan/blob/master/drift/core/telescope.py
    """


    def __init__(self):
        """Create a new UVData2Mmode"""
        self.uvbeam = None
        self.uvdata = None
        self.beam_transfer = None

    def set_beams(self,beams):
        """
        Set uvbeam object with a single beam or list of beams (for each antenna beam)
        Args:
            beams, UVBeam or AnalyticBeam object (for homogenous arrays) or list of UVBeam objects
            giving the beam at each antenna. Number of beam objects should Equal
            the number of antennas in the data set.
        """
        if isinstance(beams,UVBeam) or isinstance(beams, AnalyticBeam):
            self.uvbeam = [beams for beams in len(self.uvdata.Nants_data)]
        else:
            if len(beams) != self.uvdata.Nants_data:
                raise ValueError('Number of beams in beam list must equal number of antennas in data set.')
            else:
                self.uvbeam = beams
    def set_uv(self,uvdatasets):
        """
        Set uvdata object (or list of uvdata objects that will be cominbed).
        Args:
            uvdatasets, a UVData object or list of UVData objects
        """
        #TODO: Enforce identical antenna data and frequencies.
        if isinstance(uvdatasets,UVData):
            self.uvdata = uvdatasets
        elif isinstance(uvdatasets, list)
            self.uvdata = uvdatasets[0]
            for uvd in uvdatasets[1:]:
                self.uvdata.add(uvd)
        else:
            raise ValueError("Must provide a UVData object or list of UVData objects")

    def from_transit_telescope_and_timestream():
        '''
        create uvdata object from transit telescope object and time-stream data
        '''
        return None

    def write_timestream(self):
        '''
        export uvdata object to an mmode time-stream
        '''
        return None

    def write_transfer_matrices(self,directory):
        '''
        Write out transfer matrices
        '''
        self.beam_transfer = BeamTransfer()



    def to_transit_telescope(self, directory):
        """Telescope Export beam transfer matrix"""
        #check that self.uvdata and self.uvbeam have been properly initialized
        self.uvdata.check()
        self.uvbeam.check()
        lat,lon,alt=self.uvdata.telescope_location_lat_lon_alt_degrees

        #create abstract telescope class
        class MyPolarisedTelescope(SimplePolarisedTelescope):
            #TODO: Implement multiple beams for multiple tiles.
            def beamx(feed, freq):
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
                return self.uvbeam[feed].interp(self._angpos[:,1],self._angpos[:,0],freq)[:,0,0,0,:].squeeze().T
            def beamy(feed, freq):
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
                return self.uvbeam[feed].interp(self._angpos[:,1],self._angpos[:,0],freq)[:,0,1,0,:].squeeze().T
               # Set the feed array of feed positions (in metres EW, NS)
        @property
        def _single_feedpositions(self):
            #Do DriftScanTelescopes support 3d antenna positions?
            pos = self.uvdata.get_ENU_antpos(pick_data_ants=True)[:,:-1]
            return pos

        self.beam_transfer = BeamTransfer()
        self.beam_transfer.telescope = MyPolarisedTelescope()
        self.beam_transfer.directory = directory

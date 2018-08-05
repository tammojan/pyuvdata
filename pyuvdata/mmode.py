'''
mmat is a wrapper class for a UVbeam object and UVdata object with functions
to export uvdata objects to m-mode analysis beam-transfer matrices.

Functionality will hopefully eventually include importing m-mode data-sets
and reading/writing uvdata to m-mode time-streams.

requires the driftscan library to be installed
'''

from caput import config
from caput import time as ctime
from uvdata import UVData
import uvbeam as UVBeam
from driftscan.core.telescope import SimplePolarisedTelescope

class UVData2Mmode():
    """
    Class Defining a uvdata+uvbeam object for export to an m-mode analysis
    """


    def __init__(self):
        """Create a new UVData2Mmode"""

        self.uvd = UVData()
        self.uvb = UVBeam()

    def export_transit():
        """Telescope Export beam transfer matrix"""
        #check that self.uvd and self.uvb have been properly initialized
        self.uvd.check()
        self.uvb.check()
        lat,lon,alt=self.uvd.telescope_location_lat_lon_alt_degrees

        #create abstract telescope class
        class MyPolarisedTelescope(SimplePolarisedTelescope):
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
                return self.uvb.to_healpix()
            def beamy(feed, freq):

"""Class for reading and writing casa measurement sets."""
from astropy import constants as const
from astropy.time import Time
import numpy as np
import warnings
from uvdata import UVData
import parameter as uvp
import casacore
import casacore.tables


class MS(UVData):
    """
    Defines a class for reading and writing casa measurement sets.
    Attributs:
      ms_required_extra: Names of optional MSParameters that are required for casa ms
    """

    ms_required_extra=['data_column']
    """
    Read in data from a ms file.
    Args:
    filename:  The ms file to read from.
    run_check: Option to check for the existence and proper shapes of required parameters after reading in the file. Default is True. 
    run_sanity_check: Option to sanity check the values of the required parameters after reading in the file. Default is True. 
    """

    def __init__(self):
        #add the UVParameters to the class

        #standard angle tolerance: 10 mas in radians
        #Apparently there are plans to reduce this to 1mas
        radian_tol=10*2*np.pi*1e-3/(60.0*60.0*360.)
    
    def read_ms(self,filename,run_check=True,run_sanity_check=True,data_column='DATA'):
        #set visibility units
        if(data_column=='DATA'):
            self.vis_units.value="uncalib"
        elif(data_column=='CORRECTED_DATA' or data_column=='MODEL'):
            self.vis_units.value="Jy"

        #get spectral window information
        tb_spws=casacore.tables.table(filename+'/SPECTRAL_WINDOW')
        freqs=tb_spws.getcol('CHAN_FREQ')
        self.freq_array.value=freqs
        self.Nfreqs.value=int(freqs.shape[1])
        self.channel_width.value=tb_spws.getcol('CHAN_WIDTH')[0,0]
        self.spw_array.value=n.arange(self.Nspws.value)
        tb_spws.close()
        
        #now get the data
        tb=casacore.tables.table(filename)
        times_unique=np.unique(tb.getcol('TIME'))
        self.Ntimes.value=int(len(times_unique))
        data_array=tb.getcol(data_column)
        flag_array=tb.getcol('FLAG')
        self.Nbls.value=int(self.Nblts.value/self.nTimes.value)
        #CASA stores data in complex array with dimension NbltsxNfreqsxNpols
        #-!-What about multiple spws?-!-
        if(len(data_array.shape)==3):
            data_array=np.expand_dims(data_array,axis=1)
            flag_array=np.expand_dims(flag_array,axis=1)
        self.data_array.value=data_array
        self.Npols.value=int(data_array.shape[2])
        self.uvw_array.value=tb.getcol('UVW').T
        self.ant_1_array.value=tb.getcol('ANTENNA1').astype(int32)
        self.ant_2_array.value=tb.getcol('ANTENNA2').astype(int32)
        self.basline_array.value=self.antnums_to_baseline(self.ant_1_array.value,self.ant2_array.value)
        

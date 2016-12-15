"""Class for reading and writing casa measurement sets."""
from astropy import constants as const
from astropy.time import Time
import numpy as np
import warnings
from uvdata import UVData
import parameter as uvp
import casacore.tables as tables
import telescopes

polDict={1:1,2:2,3:3,4:4,5:-1,6:-2,7:-3,8:-4,9:-4,10:-5,11:-6,12:-8}


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
        self.Nspws.value=int(freqs.shape[0])
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
        #Get times. MS that I'm used to are modified Julian dates in seconds (thanks to Danny Jacobs for figuring out the proper conversion)
        self.time_array.value=time.Time(tb.getcol('TIME')/(3600.*24.),format='mjd').jd
        #Polarization array
        tbPol=tables.table(filename+'.ms/POLARIZATION')
        self._polarization_array.value=polDict[tbPOl.getcol('CORR_TYPE')].astype(int)
        tbPol.close()
        #Integration time
        #use first interval and assume rest are constant (though measurement set has all integration times for each Nblt )
        self._integration_time.value=tb.getcol('INTERVAL')[0]


        #open table with antenna location information
        tbAnt=tables.table(filename+'.ms/ANTENNA')
        #antenna names
        self._antenna_names.value=tbAnt.getcol('NAME')
        #Source Field
        self._antenna_numbers.value=np.unique(tbAnt.getcol('ANTENNA1')).astype(int)
        #Telescope Name

        #Instrument
        self._instrument.value=tbAnt.getcol('STATION')[0]
        self._telescope_name.value=tbAnt.getcol('STATION')[0]
        #Use Telescopes.py dictionary to set array position
        try:
            thisTelescope=telescopes.get_telescope(self.instrument.value)
            self.telescope_location_lat_lon_alt_degrees.value=(np.degrees(thisTelescope['latitude']),np.degrees(thisTelescope['longitutde']),thisTelescope['altitude'])
        except:
            #If Telescope is unknown, use median ITRF Positions of antennas
            self.telescope_location.value=np.array([np.median(tbAnt.getcol('POSITION')[:,mm]) for mm in range(3)])
        tbAnt.close()
        tbField=tables.table(filename+'.ms/FIELD')
        if(tbField.getcol('PHASE_DIR').shape[1]>1):
            self._phase_type.value='drift'
        elif(tbField.getcol('PHASE_DIR').shape[1]==1):
            self._phase_type.value='phased'
        #else:
        #    self._phase_type.value='unknown'
        #set LST array from times and itrf
        self.set_lsts_from_time_array()
            
            
        
        

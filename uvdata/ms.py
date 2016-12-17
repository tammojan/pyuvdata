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
        self.Nants_data.value=len(np.unique(self.ant_1_array))
        self.basline_array.value=self.antnums_to_baseline(self.ant_1_array.value,self.ant2_array.value)
        #Get times. MS that I'm used to are modified Julian dates in seconds (thanks to Danny Jacobs for figuring out the proper conversion)
        self.time_array.value=time.Time(tb.getcol('TIME')/(3600.*24.),format='mjd').jd
        #Polarization array
        tbPol=tables.table(filename+'.ms/POLARIZATION')
        self.polarization_array.value=polDict[tbPOl.getcol('CORR_TYPE')].astype(int)
        tbPol.close()
        #Integration time
        #use first interval and assume rest are constant (though measurement set has all integration times for each Nblt )
        self.integration_time.value=tb.getcol('INTERVAL')[0]
        #open table with antenna location information
        tbAnt=tables.table(filename+'.ms/ANTENNA')
        #antenna names
        self.antenna_names.value=tbAnt.getcol('NAME')
        self.Nants_telescope=len(self.antenna_names)
        #Source Field
        self.antenna_numbers.value=np.unique(tbAnt.getcol('ANTENNA1')).astype(int)
        #Telescope Name
        #Instrument
        self.instrument.value=tbAnt.getcol('STATION')[0]
        self.telescope_name.value=tbAnt.getcol('STATION')[0]
        #Use Telescopes.py dictionary to set array position
        self.antenna_positions=np.array(tbAnt.getcol('POSITION')-np.mean(tbAnt.getcol('POSITION'),axis=1))
        try:
            thisTelescope=telescopes.get_telescope(self.instrument.value)
            self.telescope_location_lat_lon_alt_degrees.value=(np.degrees(thisTelescope['latitude']),np.degrees(thisTelescope['longitutde']),thisTelescope['altitude'])
            self.telescope_location.value=np.array(np.mean(tbAnt.getcol('POSITION'),axis=1))
        except:
            #If Telescope is unknown, use mean ITRF Positions of antennas
            self.telescope_location.value=np.array(np.mean(tbAnt.getcol('POSITION'),axis=1))
        tbAnt.close()
        tbField=tables.table(filename+'.ms/FIELD')
        if(tbField.getcol('PHASE_DIR').shape[1]>1):
            self.phase_type.value='drift'
        elif(tbField.getcol('PHASE_DIR').shape[1]==1):
            self.phase_type.value='phased'
        #else:
        #    self.phase_type.value='unknown'
        #set LST array from times and itrf
        self.set_lsts_from_time_array()

        ##WARNING!!##
        ##YOU ARE NOW ENTERING THE FUDGE ZONE!##
        ##The following parameters need to be updated##
        ##!!##NEED TO FIGURE OUT WHAT HISTORY MEANS. SETTING AS AN EMPTY STRING FOR NOW##!!##
        self.history=''
        ##!!##NOT SURE WHETHER CASA KEEPS TRACK OF NSAMPLES, SETTING EQUAL TO ONE FOR NOW##!!##
        self.nsample_array=np.ones(self.data_array.shape)
        ##!!##SET OBJECT TO BLANK FOR NOW##!!##
        self.object_name=''
        tb.close()
        
        
            
        
    def write_ms(self,filename,spoof_nonessential=False,force_phase=False,run_check=True,run_sanity_check=True):
        """
        Write the data to a measurement set.
        Args:
        filename: measurement set to write to.
        spoof_nonessential: Option to spoof the values of optional UVParameters that are not set but are required for measurement sets.
        Default is False. 
        force_phase: Option to automatically phase drift scan data to zenith of the first timestamp. Default is False. 
        run_check: Option to check for the existence and proper shapes of required parameters before writing the file. Default is True.
        run_sanity_checK: Option to sanity check the values of required parameters before writing the file. Default is True.
        """
        if run_check:
            

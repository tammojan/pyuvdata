"""Class for reading and writing casa measurement sets."""
from astropy import constants as const
from astropy.time import Time
import numpy as np
import warnings
from uvdata import UVData
import parameter as uvp
import casacore.tables as tables
import telescopes

polDict={1:1,2:2,3:3,4:4,5:-1,6:-2,7:-3,8:-4,9:-5,10:-6,11:-7,12:-8}
#convert from casa stokes integers to pyuvdata
poLDictI={1:1,2:2,3:3,4:4,-1:5,-2:6,-3:7,-4:8,-5:9,-6:10,-7:11,-8:12}
#convert from pyuvdata to stokes casa integers

polStrDict{1:'I',2:'Q',3:'U',4:'V',
           5:'RR',6:'RL',7:'LR',8:'LL',
           9:'XX',10:'XY',11:'YX',12:'YY',
           13:'RX',14:'RY',15:'LX',16:'LY',
           17:'XR',18:'XL',19:'YR',20:'YL',
           21:'PP',22:'PQ',23:'QP',24:'QQ',
           25:'RCircular',26:'LCircular',27:'Linear',28:'Ptotal',
           29:'PFTotal',30:'PFLinear',31:'Pangle'}

'''
creates a casa table description from a dictionary of column names and data values

'''


def create_table_desc(column_dictionary):
    desc_list=[]
    for col_name in column_dictionary.keys():
        data_type=str(type(column_dictionary[col_name]))
        if(data_type=='str' or data_type=='int' or data_type=='float' or data_type=='complex'):
            desc_list.append(tables.makescacoldesc(col_name,column_dictionary[col_name]))
        elif(data_type=='list'):
            desc_list.append(tables.makescacoldesc(col_name,column_dictionary[col_name][0]))
        elif(data_type=='np.ndarray'):
            ndim=column_dictionary[col_name].ndim-1
            if(ndim>0):#if number of dimensions is greater than one, should store in an array column
                dval=column_dictionary[col_name]#Isolate a single to use as example value for column
                for mm in range(ndim+1):
                    dval=dval[mm]
                #add column description to description list
                desc_list.append(tables.makearrcoldesc(col_name,dval,ndim=ndim))
            else:
                #otherwise, create a scalar column
                desc_list.append(tables.makescacoldesc(col_name,column_dictionary[col_name][0]))
    #return a table description
    return tables.maketabdesc(desc_list)
                                    
'''
creates a casa table and writes to disk
does not return anything (should I change this?)
table_name: name of the table 
column_dictionary: dictionary with column names as keys referencing column data
keyword_dictionary: dictionary of keywords with keyword names as keys, referencing values of keywords. 
example:
nrows: number of rows in table
create_table('mytable.ms',{'DATA':np.ndarray([[[0.+1j]]]),'UVW':np.ndarray([[0.,0.,0.]])},{'MS_VERSION':2.0},1)
'''

def create_table(table_name,column_dictionary,keyword_dictionary,nrows):
    #create table
    tab_desc=create_table_desc(column_dictionary)
    tb=tables.table(table_name,tab_desc)
    #add data
    for col_name in column_dictionary.keys():
        tb.putcol(col_name,column_dictionary[col_name])
    #add keywords
    for keyword in keyword_dictionary.keys():
        tb.putkeyword(keyword,keyword_dictionary[keyword])
    tb.flush()
    tb.close()
    #write to disk

class MS(UVData):
    """
    Defines a class for reading and writing casa measurement sets.
    Attributs:
      ms_required_extra: Names of optional MSParameters that are required for casa ms
    """

    ms_required_extra=['data_column','dish_diameters','flag_row','mount']
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

        elif(data_column=='CORRECTED_DATA'):
            self.vis_units.value="Jy"

        elif(data_column=='MODEL'):
            self.vis_units.value="Jy"
        self.data_column.value=data_column
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
        self.polarization_array.value=polDict[tbPol.getcol('CORR_TYPE')].astype(int)
        tbPol.close()
        #Integration time
        #use first interval and assume rest are constant (though measurement set has all integration times for each Nblt )
        self.integration_time.value=tb.getcol('INTERVAL')[0]
        #open table with antenna location information
        tbAnt=tables.table(filename+'/ANTENNA')
        #antenna names
        self.antenna_names.value=tbAnt.getcol('NAME')
        self.Nants_telescope.value=len(self.antenna_names)
        self.dish_diameters.value=tbAnt.getcol('DISH_DIAMETER')
        self.flag_row.value=tbAnt.getcol('FLAG_ROW')
        self.mount.value=tbAnt.getcol('MOUNT')
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
        
        
    """
    !!Todo: 
    Rewrite write_ms as a series of calls to a single method 
    def create_table(<dictionary of column names with values>,<dictionary of keywords with values>)
    """

        
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
        #create MAIN table:
        #Only one spectral window is supported so far. 
        create_table(filename,
                     {self.data_column.value:self.data_array.squeeze(),
                      'ANTENNA1':self.ant_1_array.value,
                      'ANTENNA2':self.ant_2_array.value,
                      'UVW':self.uvw_array.value.T,
                      'INTERVAL':self.integration_time.value*np.ones(self.Nblts),
                      'EXPOSURE':self.integration_time.value*np.ones(self.Nblts),
                      'TIME':time.Time(self.time_array.value,format='jd').mjd*3600.*24.,
                      'TIME_CENTROID':time.Time(self.time_array.value,format='jd').mjd*3600.*24.,
                      'WEIGHT_SPECTRUM':np.ones(self.Nfreqs.value),
                      'FLAG':self.flag_array.value.squeeze(),
                      'WEIGHT':self.nsample_array.value.squeeze()},##Need to make sure this is the right thing to use for weights!
                     {'MS_VERSION':2.0},
                     self.Nblts.value)
        #create ANTENNA table:
        create_table(filename+'/ANTENNA',
                     {'OFFSET':np.zeros((self.Nant_telescope,3)),#FUDGE ALERT
                      'POSITION':self.anetnna_position.value+self.telescope_location.value,
                      'TYPE':['GROUND-BASED' for mm in range(self.Nants_telescope)],
                      'DISH_DIAMETER':self.dish_diameters.value,
                      'FLAG_ROW':self.flag_row.value,
                      'STATION':np.array([self.telescope_name.value for mm in range(self.Nants_telescope)]),
                      'MOUNT':self.mount.value,
                      'NAME':self.antenna_names.value},
                     {},self.Nants_telescope.value)
        #create DATA_DESC table:
        create_table(filename+'/DATA_DESCRIPTION',
                    {'FLAG_ROW':np.array([False]),
                     'POLARIZATION_ID':np.array([0]).astype(int),
                     'SPECTRAL_WINDOW_ID':np.array([0]).astype(int)},
                     {},1)
        #create FEED table Spoof:
        create_table(filename+'/FEED',
                     {'ANTENNA_ID':np.arange(self.Nants_telescope).astype(int),
                      'FEED_ID':np.zeros(self.Nants_telescope).astype(int),
                      'SPECTRAL_WINDOW_ID':np.zeros(self.Nants_telescope).astype(int),
                      'TIME':time.Time(np.unique(self.time_array.value)[int(np.ceil(self.Ntimes/2))],format='jd').mjd*3600.*24.,
                      'INTERVAL':np.zeros(self.Nants_telescope),
                      'NUM_RECEPTORS':np.ones(self.Nants_telescope).astype(int)*2,#Need to generalize
                      'BEAM_ID':np.zeros(self.Nants_telescope).astype(int),
                      'BEAM_OFFSET':np.zeros((self.Nants_telescope,2,2)),
                      'POLARIZATION_TYPE':np.array([[polStrDict[polDictI[self.polarization_array.value[0]]][0],polStrDict[polDictI[self.polarization_array.value[-1]]][0]] for mm in range(self.Nants_telescope)]),#pyuvdata does not allow for different pols for differnet antennas. Assumes that the last numer in pyuvdata correlation table has second feed on antenna_1. 
                      'POL_RESPONSE':np.array([[[1.+0j,0.+0j],[0.+0j,1.+0j]] for mm in range(self.Nants_telescope)])#spoof
                      'POSITION':np.zeros((self.Nants_telescope,3)),
                      
                      '
        
        
        
        
            

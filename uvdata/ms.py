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

    ms_required_extra=[]
    """
    Read in data from a ms file.
    Args:
    filename:  The ms file to read from.
    run_check: Option to check for the existence and proper shapes of required parameters after reading in the file. Default is True. 
    run_sanity_check: Option to sanity check the values of the required parameters after reading in the file. Default is True. 
    """

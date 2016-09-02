"""
Define UVParameters: data and metadata objects for interferometric data sets.

UVParameters are objects to hold specific data and metadata associated with
interferometric data sets. They are used as attributes for classes based on
UVBase. This module also includes specialiazed sublasses for particular types
of metadata.
"""
import numpy as np
import utils


class UVParameter(object):
    """
    Data and metadata objects for interferometric data sets.

    Attributes:
        name: A string giving the name of the attribute. Used as the associated
            property name in classes based on UVBase.

        required: A boolean indicating whether this is required metadata for
            the class with this UVParameter as an attribute. Default is True.

        value: The value of the data or metadata.

        spoof_val: A fake value that can be assigned to a non-required
            UVParameter if the metadata is required for a particular file-type.
            This is not an attribute of required UVParameters.

        form: Either 'str' or a tuple giving information about the expected
            shape of the value. Elements of the tuple may be the name of other
            UVParameters that indicate data shapes. \n
            Examples:\n
                'str': a string value\n
                ('Nblts', 3): the value should be an array of shape: Nblts (another UVParameter name), 3

        description: A string description of the data or metadata in the object.

        expected_type: The type that the data or metadata should be.
            Default is np.int or str if form is 'str'

        sane_vals: Optional. Tuple giving a range of reasonable values for elements of value.

        tols: Tolerances for testing the equality of UVParameters. Either a
            single absolute value or a tuple of relative and absolute values to
            be used by np.isclose()
    """

    def __init__(self, name, required=True, value=None, spoof_val=None,
                 form=(), description='', expected_type=np.int, sane_vals=None,
                 tols=(1e-05, 1e-08)):
        """Init UVParameter object."""
        self.name = name
        self.required = required
        # cannot set a spoof_val for required parameters
        if not self.required:
            self.spoof_val = spoof_val
        self.value = value
        self.description = description
        self.form = form
        if self.form == 'str':
            self.expected_type = str
        else:
            self.expected_type = expected_type
        self.sane_vals = sane_vals
        if np.size(tols) == 1:
            # Only one tolerance given, assume absolute, set relative to zero
            self.tols = (0, tols)
        else:
            self.tols = tols  # relative and absolute tolerances to be used in np.isclose

    def __eq__(self, other):
        """Equal if classes match and values are identical."""
        if isinstance(other, self.__class__):
            # only check that value is identical
            if not isinstance(self.value, other.value.__class__):
                print('{name} parameter value classes are different. Left is '
                      '{lclass}, right is {rclass}'.format(name=self.name,
                                                           lclass=self.value.__class__,
                                                           rclass=other.value.__class__))
                return False
            if isinstance(self.value, np.ndarray):
                if self.value.shape != other.value.shape:
                    print('{name} parameter value is array, shapes are '
                          'different'.format(name=self.name))
                    return False
                elif not np.allclose(self.value, other.value,
                                     rtol=self.tols[0], atol=self.tols[1]):
                    print('{name} parameter value is array, values are not '
                          'close'.format(name=self.name))
                    return False
            else:
                str_type = False
                if isinstance(self.value, (str, unicode)):
                    str_type = True
                if isinstance(self.value, list):
                    if isinstance(self.value[0], str):
                        str_type = True

                if not str_type:
                    try:
                        if not np.isclose(np.array(self.value),
                                          np.array(other.value),
                                          rtol=self.tols[0], atol=self.tols[1]):
                            print('{name} parameter value is not a string, '
                                  'values are not close'.format(name=self.name))
                            return False
                    except:
                        if self.value != other.value:
                            print('{name} parameter value is not a string, cannot '
                                  'be cast as numpy array, is not equal.'.format(name=self.name))
                            return False

                else:
                    if self.value != other.value:
                        if not isinstance(self.value, list):
                            if self.value.replace('\n', '') != other.value.replace('\n', ''):
                                print('{name} parameter value is a string (not '
                                      'a list), values are different'.format(name=self.name))
                                return False
                        else:
                            print('{name} parameter value is a list of strings, '
                                  'values are different'.format(name=self.name))
                            return False

            return True
        else:
            print('{name} parameter classes are different'.format(name=self.name))
            return False

    def __ne__(self, other):
        """Not equal."""
        return not self.__eq__(other)

    def apply_spoof(self):
        """Set value to spoof_val for non-required UVParameters."""
        self.value = self.spoof_val

    def expected_shape(self, uvbase):
        """
        Get the expected shape of the value based on the form.

        Args:
            uvbase: object with this UVParameter as an attribute. Needed
                because the form can refer to other UVParameters on this object.

        Returns:
            The expected shape of the value.
        """
        if self.form == 'str':
            return self.form
        elif isinstance(self.form, np.int):
            # Fixed shape, just return the form
            return self.form
        else:
            # Given by other attributes, look up values
            eshape = ()
            for p in self.form:
                if isinstance(p, np.int):
                    eshape = eshape + (p,)
                else:
                    val = getattr(uvbase, p)
                    if val is None:
                        raise ValueError('Missing UVBase parameter {p} needed to '
                                         'calculate expected shape of parameter'.format(p=p))
                    eshape = eshape + (val,)
            return eshape

    def sanity_check(self):
        """Check that values are sane."""
        if self.sane_vals is None:
            return True
        else:
            if self.expected_type is str:
                if self.value.lower() in (vals.lower() for vals in self.sane_vals):
                    return True
            else:
                testval = np.mean(np.abs(self.value))
                if (testval >= self.sane_vals[0]) and (testval <= self.sane_vals[1]):
                    return True
        return False


class AntPositionParameter(UVParameter):
    """
    Subclass of UVParameter for antenna positions.

    Overrides apply_spoof method to generate an array of the correct shape based
    on the number of antennas on the object with this UVParameter as an attribute.
    """

    def apply_spoof(self, uvbase, antnum_name):
        """
        Set value to zeroed array of shape: number of antennas, 3.

        Args:
            uvbase: object with this UVParameter as an attribute. Needed
                to get the number of antennas.
            antnum_name: A string giving the name of the UVParameter containing
                the number of antennas.
        """
        self.value = np.zeros((getattr(uvbase, antnum_name), 3))


class AngleParameter(UVParameter):
    """
    Subclass of UVParameter for Angle type parameters.

    Adds extra methods for conversion to & from degrees (used by UVBase objects
    for _degrees properties associated with these parameters).
    """

    def degrees(self):
        """Get value in degrees."""
        if self.value is None:
            return None
        else:
            return self.value * 180. / np.pi

    def set_degrees(self, degree_val):
        """
        Set value in degrees.

        Args:
            degree_val: value in degrees to use to set the value attribute.
        """
        if degree_val is None:
            self.value = None
        else:
            self.value = degree_val * np.pi / 180.


class LocationParameter(UVParameter):
    """
    Subclass of UVParameter for Earth location type parameters.

    Adds extra methods for conversion to & from lat/lon/alt in radians or
    degrees (used by UVBase objects for _lat_lon_alt and _lat_lon_alt_degrees
    properties associated with these parameters).
    """

    def lat_lon_alt(self):
        """Get value in (latitude, longitude, altitude) tuple in radians."""
        if self.value is None:
            return None
        else:
            return utils.LatLonAlt_from_XYZ(self.value)

    def set_lat_lon_alt(self, lat_lon_alt):
        """
        Set value from (latitude, longitude, altitude) tuple in radians.

        Args:
            lat_lon_alt: tuple giving the latitude (radians), longitude (radians)
                and altitude to use to set the value attribute.
        """
        if lat_lon_alt is None:
            self.value = None
        else:
            self.value = utils.XYZ_from_LatLonAlt(lat_lon_alt[0], lat_lon_alt[1],
                                                  lat_lon_alt[2])

    def lat_lon_alt_degrees(self):
        """Get value in (latitude, longitude, altitude) tuple in degrees."""
        if self.value is None:
            return None
        else:
            latitude, longitude, altitude = utils.LatLonAlt_from_XYZ(self.value)
            return latitude * 180. / np.pi, longitude * 180. / np.pi, altitude

    def set_lat_lon_alt_degrees(self, lat_lon_alt_degree):
        """
        Set value from (latitude, longitude, altitude) tuple in degrees.

        Args:
            lat_lon_alt: tuple giving the latitude (degrees), longitude (degrees)
                and altitude to use to set the value attribute.
        """
        if lat_lon_alt_degree is None:
            self.value = None
        else:
            latitude, longitude, altitude = lat_lon_alt_degree
            self.value = utils.XYZ_from_LatLonAlt(latitude * np.pi / 180.,
                                                  longitude * np.pi / 180.,
                                                  altitude)
import math
import re


def to_empty(entry):
    """
    Converts None values to empty strings.

    Parameters:
        entry (): Any type entry.

    Returns:
        entry (): Converted value.
    """

    if entry is None:
        entry = ''
    else:
        entry = entry
    return entry


def to_none(entry):
    """
    Converts empty strings to None.

    Parameters:
        entry (): Any type entry.

    Returns:
        entry (): Converted value.
    """

    if entry == '':
        entry = None
    else:
        entry = float(entry)
    return entry


def to_m_inf(entry):
    """
    Converts empty strings or None values to -inf.

    Parameters:
        entry (): Any type entry.

    Returns:
        entry (): Converted value.
    """

    if entry is None:
        entry = float('-inf')
    elif entry == '':
        entry = '-inf'
    else:
        entry = entry
    return entry


def to_p_inf(entry):
    """
    Converts empty strings or None values to inf.

    Parameters:
        entry (): Any type entry.

    Returns:
        entry (): Converted value.
    """

    if entry is None:
        entry = float('inf')
    elif entry == '':
        entry = 'inf'
    else:
        entry = entry
    return entry


def to_zero(entry):
    """
    Converts None values to 0.

    Parameters:
        entry (): Any type entry.

    Returns:
        entry (): Converted value.
    """

    if entry is None:
        entry = 0
    else:
        entry = entry
    return entry


def check_decimal(entry):
    """
    Checks whether given string has a representation of a value with decimals.

    Parameters:
        entry (str): A string to be checked.

    Returns:
        (bool): Indicator of a decimal number.
    """

    if re.findall(r'[0-9]\.[0-9]', entry) == []:
        return False
    else:
        return True


def ra_to_float(coordinates):
    """
    Given right ascension value as either a string representing a float number or a string of the 00h00m00s format,
    return the corresponding float value.

    Parameters:
        coordinates (str | float | int): A string representing a float or 00h00m00s format right ascension.

    Returns:
        coordinates (float): Float value of right ascension.
    """

    if isinstance(coordinates, float) or isinstance(coordinates, int):
        coordinates = str(coordinates)
    if coordinates.find('s') != -1:
        h = float(coordinates[0:2])
        m = float(coordinates[3:5])
        s = float(coordinates[coordinates.find('m') + 1:coordinates.find('s')])
        return h * 15 + m / 4 + s / 240
    else:
        return float(coordinates)


def dec_to_float(coordinates):
    """
    Given right declination value as either a string representing a float number or a string of the +/-00d00m00s format,
    return the corresponding float value.

    Parameters:
        coordinates (str | float | int): A string representing a float or +/-00d00m00s format declination.

    Returns:
        coordinates (float): Float value of declination.
    """

    if isinstance(coordinates, float) or isinstance(coordinates, int):
        coordinates = str(coordinates)
    if coordinates.find('s') != -1:
        d = float(coordinates[1:3])
        m = float(coordinates[4:6])
        s = float(coordinates[coordinates.find('m') + 1:coordinates.find('s')])
        if coordinates[0] == "-":
            return (-1) * (d + m / 60 + s / 3600)
        else:
            return d + m / 60 + s / 3600
    elif coordinates == '-inf' or coordinates == 'inf':
        return float(coordinates)
    else:
        if coordinates[0] == '+':
            dec = coordinates.replace("+", "")
        else:
            dec = coordinates
        return float(dec)


def round_to_nsf(value, nsf=2):
    """
    Rounds the number to the provided number of significant figures.
    """

    integer_part = math.floor(value)
    if integer_part > 0:
        integer_part_len = len(str(integer_part))
        return round(value, nsf-integer_part_len)
    else:
        st = {'1', '2', '3', '4', '5', '6', '7', '8', '9'}
        index = next((i for i, ch in enumerate(str(value)) if ch in st), None)
        return round(value, index-2+nsf)


def round_to_uncertainty(value, pos_uncertainty, neg_uncertainty):
    """
    Among two uncertainties finds one with more precision and
    rounds the value of variable number accordingly.
    """

    if len(str(pos_uncertainty)) != len(str(neg_uncertainty)):
        uncertainty = pos_uncertainty if len(str(pos_uncertainty)) > len(str(neg_uncertainty)) else neg_uncertainty
        uncertainty_str = str(uncertainty)
    else:
        uncertainty_str = str(pos_uncertainty)
    if check_decimal(uncertainty_str):
        decimals = uncertainty_str[uncertainty_str.find('.') + 1:]
        precision = len(decimals)
    else:
        precision = len(uncertainty_str)
        for c in uncertainty_str:
            if c != '0':
                precision -= 1
            else:
                pass

    return round(value, precision)


def round_redshift(value, positive_uncertainty, negative_uncertainty, redshift=True, download=False):
    """
    Given either redshift (default behaviour) or frequency and the corresponding uncertainties,
    the function round up the values according to the specified rule:
    a) If no uncertainties are available, round to a fixed precision depending on whether the data is
    to be viewed or downloaded.
    b) If uncertainties are available, round uncertainties to 2 significant values,
    and round the redshift/frequency according to uncertainty with most precision.

    Parameters:
        value (float): redshift or observed frequency value.
        positive_uncertainty (float): corresponding positive uncertainty.
        negative_uncertainty (float): corresponding negative uncertainty.
        redshift (bool): Default:True. True if the value is redshift, False if frequency.
        download (bool): Default:False. True if the values are to be downloaded, False if to be displayed.

    Returns:
        (rounded_value, positive_uncertainty, negative_uncertainty) ((float, float, float)): Rounded up values.
    """

    if value is None:
        return None, None, None

    if (positive_uncertainty is None) or (negative_uncertainty is None):
        if (positive_uncertainty is None) and (negative_uncertainty is None):

            if not download:
                # round to 4 decimals for redshift and 6 for frequency.
                if redshift:
                    return round(value, 4), None, None
                else:
                    return round(value, 6), None, None
            else:
                # when downloading, precision higher by 2.
                if redshift:
                    return round(value, 6), None, None
                else:
                    return round(value, 8), None, None
        # if one of the uncertainties is None, we assume symmetry.
        elif negative_uncertainty is None:
            negative_uncertainty = positive_uncertainty
        else:
            positive_uncertainty = negative_uncertainty
    # now we have both uncertainties, so round to uncertainty.
    # but first round uncertainty to 2 sf.
    positive_uncertainty = round_to_nsf(positive_uncertainty, 2)
    negative_uncertainty = round_to_nsf(negative_uncertainty, 2)
    rounded_value = round_to_uncertainty(value, positive_uncertainty, negative_uncertainty)
    return rounded_value, positive_uncertainty, negative_uncertainty


def redshift_to_frequency(emitted_frequency, z, positive_uncertainty, negative_uncertainty):
    """
    Converts redshift value to frequency.

    Parameters:
        emitted_frequency (float): Emitted frequency value as per dictionary.
        z (float): Submitted redshift value.
        positive_uncertainty (float): Submitted positive uncertainty of the redshift value.
        negative_uncertainty (float): Submitted negative uncertainty of the redshift value.

    Returns:
        f (float): Observed frequency.
        f_uncertainty_positive (float | NoneType): Positive uncertainty of the f value or None
        f_uncertainty_negative (float | NoneType): Negative uncertainty of the f value or None
    """

    if z is None:
        return None, None, None
    f = emitted_frequency / (z + 1)
    if (positive_uncertainty is None) or (negative_uncertainty is None):
        if (positive_uncertainty is None) and (negative_uncertainty is None):
            return f, None, None
        elif negative_uncertainty is None:
            negative_uncertainty = positive_uncertainty
        else:
            positive_uncertainty = negative_uncertainty

    delta_z = positive_uncertainty + negative_uncertainty
    delta_f = delta_z * f / (z + 1)
    f_uncertainty_positive = positive_uncertainty / delta_z * delta_f
    f_uncertainty_negative = negative_uncertainty / delta_z * delta_f

    return f, f_uncertainty_positive, f_uncertainty_negative


def frequency_to_redshift(emitted_frequency, f, positive_uncertainty, negative_uncertainty):
    """
    Converts redshift value to frequency.

    Parameters:
        emitted_frequency (float): Emitted frequency value as per dictionary.
        f (float): Submitted observed frequency value.
        positive_uncertainty (float): Submitted positive uncertainty of the observed frequency value.
        negative_uncertainty (float): Submitted negative uncertainty of the observed frequency value.

    Returns:
        z (float): Redshift.
        z_uncertainty_positive (float | NoneType): Positive uncertainty of the z value or None
        z_uncertainty_negative (float | NoneType): Negative uncertainty of the z value or None
    """

    if f is None:
        return None, None, None
    z = emitted_frequency / f - 1
    if (positive_uncertainty is None) or (negative_uncertainty is None):
        if (positive_uncertainty is None) and (negative_uncertainty is None):
            return z, None, None
        elif negative_uncertainty is None:
            negative_uncertainty = positive_uncertainty
        else:
            positive_uncertainty = negative_uncertainty

    delta_f = positive_uncertainty + negative_uncertainty
    delta_z = delta_f * (z + 1) / f
    z_uncertainty_positive = positive_uncertainty / delta_f * delta_z
    z_uncertainty_negative = negative_uncertainty / delta_f * delta_z
    return z, z_uncertainty_positive, z_uncertainty_negative

    return z, z_uncertainty_positive, z_uncertainty_negative
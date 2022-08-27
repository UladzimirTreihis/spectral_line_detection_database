from app import db
from app.models import Freq
import re


def check_decimal(entry):
    """
    Checks whether given string has is a representation of a value with decimals.

    Parameters:
        entry (str): A string to be checked.

    Returns:
        (bool): Indicator of a decimal number.
    """

    if re.findall(r'[0-9]\.[0-9]', entry) == []:
        return False
    else:
        return True


def test_frequency(species_name_input, input_frequency_str):
    nearest_frequency = 0
    message = ''
    frequency_input = float(input_frequency_str)
    message_not_found = ' Specified species are not in our database, please check the spelling.'
    message_other_found = "Your specified frequency is not precise enough. " \
                          "We also found species ({}) has a transition ({}) at a rest frequency of ({}) GHz. " \
                          "Make sure you have entered correct species name and/or more precise frequency."

    same_species = db.session.query(Freq).filter(Freq.species == species_name_input).all()
    if not same_species:
        message = message + message_not_found
    else:
        species = species_name_input
        delta = frequency_input
        for entry in same_species:
            frequency = entry.frequency
            if abs(frequency - frequency_input) < delta:
                delta = abs(frequency - frequency_input)
                nearest_frequency = frequency

        if check_decimal(input_frequency_str):
            decimals = input_frequency_str[input_frequency_str.find('.') + 1:]
            precision = len(decimals)
            range_1 = frequency_input - 0.1 ** precision
            range_2 = frequency_input + 0.1 ** precision
        else:
            precision = len(input_frequency_str)
            for c in input_frequency_str:
                if c != '0':
                    precision -= 1
                else:
                    pass
            range_1 = frequency_input - 10 ** precision
            range_2 = frequency_input + 10 ** precision

        # Check the family / chemical name first
        chemical_name = same_species[0].chemical_name
        same_chemical_name = db.session.query(Freq).filter(Freq.chemical_name == chemical_name)
        for entry in same_chemical_name:
            if entry.species == species:
                if entry.frequency == nearest_frequency:
                    continue
                elif (entry.frequency > range_1) and (entry.frequency < range_2):
                    message = message + \
                              message_other_found.format(
                                  entry.species, entry.qn, entry.frequency)

            elif (entry.frequency > range_1) and (entry.frequency < range_2):
                message = message + \
                          message_other_found.format(
                              entry.species, entry.qn, entry.frequency)

        if message:
            nearest_frequency = False
    return nearest_frequency, message

"""
Utility that extracts component information from askap-docs rst files.
Since it is built to handle yanda components specifically, it is in this repository.

@author Nicholas Pritchard nicholas.pritchard@uwa.edu.au
"""

import argparse
import re
import copy
from enum import Enum, auto


class TableStates(Enum):
    FREE = auto()
    FIELD = auto()
    FIELD_ENDING = auto()


def parse_field_line(par_name, par_type, par_def, par_description, line):
    fields = line.split("|")[1:-1]
    for field, attribute in zip(fields, [par_name, par_type, par_def, par_description]):
        field = field.strip()
        if field != "":
            attribute.append(field)
    return par_name, par_type, par_def, par_description


def parse_lines_to_table(lines):
    """
    Tactic is to read line by line, recognizing when we are in a table -> cell -> free-space
    @warning There is no 'intelligent' parsing of in-cell text, nor is there any way to distinguish
    between tables (for now).
    :param lines: The lines to process
    :return: A dictionary containing strings for each found parameter
    """
    table_header = re.compile(r"(\+\=+){4}\+")
    end_of_table = re.compile(r"(\+\-+){4}\+")
    prefix_finder = re.compile(r"\*+.*\*+ prefix")
    output = []
    state = TableStates.FREE
    parameter_name = []
    parameter_type = []
    parameter_default = []
    parameter_description = []
    prefix = ""
    for line in lines:
        line = line.strip()
        if state == TableStates.FREE:
            if table_header.match(line):
                state = TableStates.FIELD
                print("GOING TO FIELD MODE")
            if prefix_finder.search(line):
                print("CHANGING PREFIX")
                prefix = prefix_finder.findall(line)[0].split(" ")[0].replace('*', '')

        elif state == TableStates.FIELD:
            parameter_name, parameter_type, parameter_default, parameter_description = \
                parse_field_line(parameter_name, parameter_type, parameter_default,
                                 parameter_description, line)
            if end_of_table.match(line):
                state = TableStates.FIELD_ENDING
                print("IS THE FIELD ENDING?")
        elif state == TableStates.FIELD_ENDING:
            if line == "":
                state = TableStates.FREE
                print("GOING TO FREE MODE")
            else:
                state = TableStates.FIELD
            if parameter_type != [] and parameter_default != [] and parameter_name != []:
                output.append({
                    'name': parameter_name,
                    'type': parameter_type,
                    'default': parameter_default,
                    'description': " ".join(parameter_description),
                    'prefix': copy.copy(prefix)
                })
            parameter_name = []
            parameter_type = []
            parameter_default = []
            parameter_description = []
            print("BACK TO FIELD MODE")
            parameter_name, parameter_type, parameter_default, parameter_description = \
                parse_field_line(parameter_name, parameter_type, parameter_default,
                                 parameter_description, line)
    return output


def extract_table(filename):
    with open(filename, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()
    return parse_lines_to_table(lines)


def parameter_to_xml(parameter):
    if parameter['default'] == []:
        parameter['default'] = ['None']
    if parameter['prefix'] != "":
        parameter['prefix'] = parameter['prefix'] + '.'
    if len(parameter['name']) > 1:
        parameter['name'] = ["".join(x for x in parameter['name']).replace("\\", "")]
    return f"# @param[in] param/{parameter['prefix']}{parameter['name'][0]} {parameter['prefix']}" \
           f"{parameter['name'][0]}/{parameter['default'][0]}/" \
           f"{parameter['type'][0]}/readwrite/False/{parameter['description']}\n"


def write_output(parameters, outfile):
    with open(outfile, 'a', encoding='utf-8') as ofile:
        for parameter in parameters:
            ofile.write(parameter_to_xml(parameter))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('i', type=str, help="rst file to process")
    parser.add_argument('o', type=str, help="output file")

    args = parser.parse_args()
    write_output(extract_table(args.i), args.o)

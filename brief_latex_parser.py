#!/usr/bin/python
# -*- coding: <utf-8> -*-


from pandas import read_csv
import subprocess as sp
import os
import re
import math
import ftfy
import threading

import tkinter as tk
from tkinter import filedialog

root = tk.Tk()
filename_latex = filedialog.askopenfilename(master=root,filetypes=[('tex', '.tex'), ('all files', '.*')],title='Choose tex file')
filename_table = filedialog.askopenfilename(master=root,filetypes=[('csv', '.csv'), ('all files', '.*')],title='Choose csv file')
out_directory = os.path.dirname(filename_latex)+'/output'

# out_directory = './output'
#
# filename_latex='example.tex'
# filename_table='example.csv'


table = read_csv(filename_table, error_bad_lines=True, encoding="ISO-8859-1", decimal=",", dtype=str)


def fix_encoding_table(x):
    if type(x) == str:
        return ftfy.fix_text(x)
    else:
        return x

table.applymap(fix_encoding_table)

filename_list = []

with open(filename_latex, 'r') as f:
    tex_string = ftfy.fix_text(f.read())


nec_fields = []
try:
    nec_fields_reg = re.search(r'#Necessary fields:\s*(([\w]+[\w\s]*)(,\s*[\w]+[\w\s]*)*)&', tex_string).group(1).split(',')
    for res in nec_fields_reg:
        nec_fields.append(res.replace(',', '').lstrip().rstrip())
except Exception:
    print('Could not read in necessary fields')

bool_fields = []
try:
    bool_fields_reg = re.search(r'#Output bool:\s*(([\w]+[\w\s]*)(,\s*[\w]+[\w\s]*)*)&', tex_string).group(1).split(',')
    for res in bool_fields_reg:
        bool_fields.append(res.replace(',', '').lstrip().rstrip())
except Exception:
    print('Could not read in output bool fields')

pattern_input = '([\w\s\\\{\}\[\],.~]*)'



def if_finder(in_string):
    search_res = re.findall(r'#IF\|([\w\s,.]+)\|'+pattern_input+'&', in_string, re.UNICODE)
    return search_res

def if_else_finder(in_string):
    search_res = re.findall(r'#IF\|([\w\s,.]+)\|'+pattern_input+'\|ELSE\|'+pattern_input+'&', in_string, re.UNICODE)
    return search_res

def ifnot_finder(in_string):
    search_res = re.findall(r'#IFNOT\|([\w\s,.]+)\|'+pattern_input+'&', in_string, re.UNICODE)
    return search_res


def ifequal_finder(in_string):
    search_res = re.findall(r'#IF=\|([\w\s,.]+)\|([\w\s,.]+)\|'+pattern_input+'&', in_string, re.UNICODE)
    return search_res

def ifequal_else_finder(in_string):
    search_res = re.findall(r'#IF=\|([\w\s,.]+)\|([\w\s,.]+)\|'+pattern_input+'\|ELSE\|'+pattern_input+'&', in_string, re.UNICODE)
    return search_res


def subprocess_cmd(command,print_output=False):
    process = sp.Popen(command, stdout=sp.PIPE, shell=True)
    if print_output:
        proc_stdout = process.communicate()[0].strip()
        print(proc_stdout)


def run_command_with_timeout(cmd, timeout_sec=5):
    """Execute `cmd` in a subprocess and enforce timeout `timeout_sec` seconds.

    Return subprocess exit code on natural completion of the subprocess.
    Raise an exception if timeout expires before subprocess completes."""
    proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE)
    proc_thread = threading.Thread(target=proc.communicate)
    proc_thread.start()
    proc_thread.join(timeout_sec)
    if proc_thread.is_alive():
        # Process still running - kill it and raise timeout error
        try:
            proc.kill()
        except OSError as e:
            # The process finished between the `is_alive()` and `kill()`
            return proc.returncode
        # OK, the process was definitely killed
        raise TimeoutError('Process #%d killed after %f seconds' % (proc.pid, timeout_sec))
    # Process completed naturally - return exit code
    return proc.returncode

def test_nan(in_value):
    if type(in_value) == str:
        return False
    elif type(in_value) == float:
        if math.isnan(in_value):
            return True
        else:
            return False

def str2bool(in_string):
    if in_string.lower() in ['1','true','wahr','ja']:
        return True
    else:
        return False

print('PyParser fuer latex Briefe wurde gestartet\n--------------------------------------')

for i, row in enumerate(table.iterrows()):
    if len(bool_fields) > 0:
        if not row[1][bool_fields].apply(str2bool).all():
            continue

    print('Parsing and calling latex on row {0:d} '.format(i))
    if len(nec_fields) > 0:
        if row[1][nec_fields].isnull().values.any():
            print('Necessary fields were not supplied')
            continue

    parsed_tex = tex_string
    row_dict = row[1].to_dict()
    for table_key in row_dict.keys():
        table_value = row_dict[table_key]
        if not test_nan(table_value):
            if type(table_value) == float:
                in_string = '{0:1.0f}'.format(table_value)
            else:
                in_string = str(table_value)
        else:
            in_string = ''
        parsed_tex = parsed_tex.replace('#' + table_key + '&', in_string)

    while True:
        parsed_if_statements = if_finder(parsed_tex)
        for if_key, if_input in parsed_if_statements:
            table_value = row_dict[if_key]
            if not test_nan(table_value):
                parsed_tex = parsed_tex.replace(u'#IF|' + if_key + u'|' + if_input + u'&', if_input)
            else:
                parsed_tex = parsed_tex.replace(u'#IF|' + if_key + u'|' + if_input + u'&', u'')

        parsed_if_else_statements = if_else_finder(parsed_tex)
        for if_key, if_input, else_input in parsed_if_else_statements:
            table_value = row_dict[if_key]
            if not test_nan(table_value):
                parsed_tex = parsed_tex.replace(u'#IF|' + if_key + u'|' + if_input + u'|ELSE|' + else_input + u'&',
                                                if_input)
            else:
                parsed_tex = parsed_tex.replace(u'#IF|' + if_key + u'|' + if_input + u'|ELSE|' + else_input + u'&',
                                                else_input)

        parsed_ifnot_statements = ifnot_finder(parsed_tex)
        for if_key, if_input in parsed_ifnot_statements:
            table_value = row_dict[if_key]
            if test_nan(table_value):
                parsed_tex = parsed_tex.replace(u'#IFNOT|' + if_key + u'|' + if_input + u'&', if_input)
            else:
                parsed_tex = parsed_tex.replace(u'#IFNOT|' + if_key + u'|' + if_input + u'&', u'')

        parsed_ifequal_statements = ifequal_finder(parsed_tex)
        for if_key, test_value, if_input in parsed_ifequal_statements:
            table_value = row_dict[if_key]
            if table_value == test_value:
                parsed_tex = parsed_tex.replace(u'#IF=|' + if_key + u'|' + test_value + u'|' + if_input + u'&',
                                                if_input)
            else:
                parsed_tex = parsed_tex.replace(u'#IF=|' + if_key + u'|' + test_value + u'|' + if_input + u'&', u'')

        parsed_ifequal_else_statements = ifequal_else_finder(parsed_tex)
        for if_key, test_value, if_input, else_input in parsed_ifequal_else_statements:
            table_value = row_dict[if_key]
            if table_value == test_value:
                parsed_tex = parsed_tex.replace(
                    u'#IF=|' + if_key + u'|' + test_value + u'|' + if_input + u'|ELSE|' + else_input + u'&', if_input)
            else:
                parsed_tex = parsed_tex.replace(
                    u'#IF=|' + if_key + u'|' + test_value + u'|' + if_input + u'|ELSE|' + else_input + u'&', else_input)

        if len(parsed_if_statements) == 0 and len(parsed_ifnot_statements) == 0 and len(
                parsed_ifequal_statements) == 0 and len(parsed_ifequal_else_statements) == 0 and len(
                parsed_if_else_statements) == 0:
            break

    parsed_tex = parsed_tex.replace('ß',r'{\ss}')

    if not os.path.exists(out_directory):
        os.makedirs(out_directory)

    with open(out_directory + '/parsed' + str(i) + '.tex', 'w') as f:
        f.write(parsed_tex)

    try:
        return_code = run_command_with_timeout('cd ' + out_directory + '&pdflatex parsed' + str(i) + '.tex -interaction=nonstopmode')
        if return_code == 0:
            filename_list.append('parsed' + str(i) + '.pdf')
            print('Success')
        else:
            print("Latex did not compile not successfully")
    except TimeoutError:
        print('Latex timeout after 5 seconds. Continuing with next row. Press ctrl+c to abort')
        continue

    print('')

print('')
print('Finished with single files. Now appending to main.pdf')

main_tex = r"""
\documentclass[a4paper]{article}
\usepackage{pdfpages}
\begin{document}

"""

for filename in filename_list:
    main_tex += r'\includepdf[fitpaper,pages=-]{' + filename + '}\n'

main_tex += r'\end{document}'

with open(out_directory + '/main.tex', 'w') as f:
    f.write(main_tex)


try:
    return_code = run_command_with_timeout('cd ' + out_directory + '&pdflatex main.tex -interaction=nonstopmode',timeout_sec=120)
    if return_code == 0:
        print('Success. {0:d} letters were joined into main.pdf'.format(len(filename_list)))
    else:
        print("Latex did not compile not successfully")

except TimeoutError:
    print('Latex timeout after 120 seconds.')


root.destroy()

#!/usr/bin/python
# -*- coding: <utf-8> -*-


from pandas import read_csv
import subprocess as sp
import os
import re
import math

import tkinter as tk
from tkinter import filedialog

root = tk.Tk()

filename_latex  = filedialog.askopenfilename(master=root,filetypes=[('tex', '.tex'), ('all files', '.*')],title='Choose tex file')

out_directory = os.path.dirname(filename_latex)+'/output'

filename_table = filedialog.askopenfilename(master=root,filetypes=[('csv', '.csv'), ('all files', '.*')],title='Choose csv file')
table = read_csv(filename_table, error_bad_lines=True, encoding="ISO-8859-1", decimal=",")

filename_list = []

with open(filename_latex, 'r') as f:
    tex_string = f.read()

nec_fields = []
try:
    nec_fields_reg = re.search(r'#Necessary fields:\s*((\w+)(,\s*\w+)*)', tex_string).group(1).split(',')
    for res in nec_fields_reg:
        nec_fields.append(res.replace(',', '').lstrip().rstrip())
except:
    print('Could not read in necessary fields')


def if_finder(in_string):
    search_res = re.findall(r'#IF:([\w\s]+):([\w\s\\\{\}\[\],.]*)#', in_string, re.UNICODE)
    return search_res


def subprocess_cmd(command,print_output=False):
    process = sp.Popen(command, stdout=sp.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    if print_output:
        print(proc_stdout)


def test_nan(in_value):
    if type(in_value) == str:
        return False
    elif type(in_value) == float:
        if math.isnan(in_value):
            return True
        else:
            return False

print('PyParser fuer latex Briefe wurde gestartet\n--------------------------------------')

for i, row in enumerate(table.iterrows()):
    print('Parsing row {0:d} '.format(i))
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
        parsed_tex = parsed_tex.replace('#' + table_key + '#', in_string)

    parsed_if_statements = if_finder(parsed_tex)

    for if_key, if_input in parsed_if_statements:
        table_value = row_dict[if_key]
        if not test_nan(table_value):
            parsed_tex = parsed_tex.replace('#IF:' + if_key + ':' + if_input + '#', if_input)
        else:
            parsed_tex = parsed_tex.replace('#IF:' + if_key + ':' + if_input + '#', '')

    parsed_tex = parsed_tex.replace('ß',r'{\ss}')

    if not os.path.exists(out_directory):
        os.makedirs(out_directory)

    with open(out_directory + '/parsed' + str(i) + '.tex', 'w') as f:
        f.write(parsed_tex)
    print('Calling latex')
    subprocess_cmd('cd ' + out_directory + '&pdflatex parsed' + str(i) + '.tex')
    filename_list.append('parsed' + str(i) + '.pdf')
    print('')

print('')
print('Finished parsing Files\nNow latex is called')

main_tex = r"""
\documentclass{article}
\usepackage{pdfpages}
\begin{document}

"""

for filename in filename_list:
    main_tex += r'\includepdf[pages=-]{' + filename + '}\n'

main_tex += r'\end{document}'

with open(out_directory + '/main.tex', 'w') as f:
    f.write(main_tex)

subprocess_cmd('cd ' + out_directory + '&pdflatex main.tex')
print('Finished')
# messagebox.showinfo(master=root,message='Program finished')


root.destroy()

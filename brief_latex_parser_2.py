#!/usr/bin/python
# -*- coding: <utf-8> -*-

from __future__ import with_statement
from __future__ import absolute_import
from pandas import read_csv
import subprocess as sp
import os
import re
import math

import Tkinter as tk
import tkFileDialog as filedialog
from io import open

root = tk.Tk()

filename_latex  = filedialog.askopenfilename(master=root,filetypes=[(u'tex', u'.tex'), (u'all files', u'.*')],title=u'Choose tex file')

out_directory = os.path.dirname(filename_latex)+u'/output'

filename_table = filedialog.askopenfilename(master=root,filetypes=[(u'csv', u'.csv'), (u'all files', u'.*')],title=u'Choose csv file')
table = read_csv(filename_table, error_bad_lines=True, encoding=u"ISO-8859-1", decimal=u",")

filename_list = []

with open(filename_latex, u'r') as f:
    tex_string = f.read()

nec_fields = []
try:
    nec_fields_reg = re.search(ur'#Necessary fields:\s*((\w+)(,\s*\w+)*)', tex_string).group(1).split(u',')
    for res in nec_fields_reg:
        nec_fields.append(res.replace(u',', u'').lstrip().rstrip())
except:
    print u'Could not read in necessary fields'


def if_finder(in_string):
    search_res = re.findall(ur'#IF:([\w\s]+):([\w\s\\\{\}\[\],.]*)#', in_string, re.UNICODE)
    return search_res

def ifnot_finder(in_string):
    search_res = re.findall(ur'#IFNOT:([\w\s]+):([\w\s\\\{\}\[\],.]*)#', in_string, re.UNICODE)
    return search_res

def ifequal_finder(in_string):
    search_res = re.findall(ur'#IF=:([\w\s]+):([\w\s]+):([\w\s\\\{\}\[\],.]*)#', in_string, re.UNICODE)
    return search_res


def subprocess_cmd(command,print_output=False):
    process = sp.Popen(command, stdout=sp.PIPE, shell=True)
    proc_stdout = process.communicate()[0].strip()
    if print_output:
        print proc_stdout


def test_nan(in_value):
    if type(in_value) == unicode:
        return False
    elif type(in_value) == float:
        if math.isnan(in_value):
            return True
        else:
            return False

print u'PyParser fuer iScientist wurde gestartet\n--------------------------------------'

for i, row in enumerate(table.iterrows()):
    print u'Parsing row {0:d} '.format(i)
    if len(nec_fields) > 0:
        if row[1][nec_fields].isnull().values.any():
            print u'Necessary fields were not supplied'
            continue

    parsed_tex = tex_string
    row_dict = row[1].to_dict()
    for table_key in row_dict.keys():
        table_value = row_dict[table_key]
        if not test_nan(table_value):
            if type(table_value) == float:
                in_string = u'{0:1.0f}'.format(table_value)
            else:
                in_string = unicode(table_value)
        else:
            in_string = u''
        parsed_tex = parsed_tex.replace(u'#' + table_key + u'#', in_string)

    parsed_if_statements = if_finder(parsed_tex)
    for if_key, if_input in parsed_if_statements:
        table_value = row_dict[if_key]
        if not test_nan(table_value):
            parsed_tex = parsed_tex.replace(u'#IF:' + if_key + u':' + if_input + u'#', if_input)
        else:
            parsed_tex = parsed_tex.replace(u'#IF:' + if_key + u':' + if_input + u'#', u'')

    parsed_ifnot_statements = ifnot_finder(parsed_tex)
    for if_key, if_input in parsed_ifnot_statements:
        table_value = row_dict[if_key]
        if test_nan(table_value):
            parsed_tex = parsed_tex.replace(u'#IFNOT:' + if_key + u':' + if_input + u'#', if_input)
        else:
            parsed_tex = parsed_tex.replace(u'#IFNOT:' + if_key + u':' + if_input + u'#', u'')

    parsed_ifequal_statements = ifequal_finder(parsed_tex)
    for if_key,test_value, if_input in parsed_ifequal_statements:
        table_value = row_dict[if_key]
        if table_value == test_value:
            parsed_tex = parsed_tex.replace(u'#IF=:'+if_key+u':' +  test_value+ u':' + if_input + u'#', if_input)
        else:
            parsed_tex = parsed_tex.replace(u'#IF=:'+if_key+u':' + test_value + u':' + if_input + u'#', u'')

    parsed_tex = parsed_tex.replace(u"\u00DF",ur'{\ss}')
    parsed_tex = parsed_tex.replace(u"\u00FC",ur'\"u')
    parsed_tex = parsed_tex.replace(u"\u00DC",ur'\"U')
    parsed_tex = parsed_tex.replace(u"\u00E4",ur'\"a')
    parsed_tex = parsed_tex.replace(u"\u00C4",ur'\"A')
    parsed_tex = parsed_tex.replace(u"\u00F6",ur'\"o')
    parsed_tex = parsed_tex.replace(u"\u00D6",ur'\"O')

    if not os.path.exists(out_directory):
        os.makedirs(out_directory)

    with open(out_directory + u'/parsed' + unicode(i) + u'.tex', u'w') as f:
        f.write(parsed_tex)

    print u'Calling latex'
    subprocess_cmd(u'cd ' + out_directory + u';pdflatex parsed' + unicode(i) + u'.tex')
    filename_list.append(u'parsed' + unicode(i) + u'.pdf')
    print u''


print u''
print u'Finished parsing Files\nNow latex is called'

main_tex = r'\documentclass{article}'+'\n' + r'\usepackage{pdfpages}' +'\n' + r'\begin{document}'

for filename in filename_list:
    main_tex += r'\includepdf[pages=-]{' + filename + u'}\n'

main_tex += r'\end{document}'

with open(out_directory + u'/main.tex', u'w') as f:
    f.write(main_tex)

subprocess_cmd(u'cd ' + out_directory + u';pdflatex main.tex')
print u'Finished'
# messagebox.showinfo(master=root,message='Program finished')


root.destroy()

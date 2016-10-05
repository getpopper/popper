#! /usr/bin/env python

#####################
# convert output from mpip to CSV.
# Taken from https://github.com/minimalmetrics/mmperftools
#####################
#
# Copyright (c) 2015 Philip Mucci, Tushar Mohan
# {mucci@cs.utk.edu, tusharmohan@gmail.com}
#
# This software is distributed under the MIT license.
#
# ******IMPORTANT******
# Please note, while building the tools, additional open-source software will be
# downloaded. This license does not apply to software downloaded during the
# build process, which is accompanied with its own licenses. This software
# also includes some test programs that have their own licenses. In such cases
# the license accompanying the individual component will override this license
# for the particular component.
# *********************
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import argparse
import os.path
import sys

def names():
    list = []
    for key in sdict.keys():
        name = sdict[key]['name']
        limit = name.find(')')
        if limit is -1 : list.append(name)
        else: list.append(name[:limit])
    return list

def revnames():
    list = []
    for key in sdict.keys():
        name = sdict[key]['name']
        limit = name.find(')')
        if limit is -1 : list.append((name,key))
        else: list.append((name[:limit],key))
    return dict(list)

def parse_section_MPI_TIME(lines):
    #           0       1          2           3
    col_list = 'Task    AppTime    MPITime     MPI-pct'.split()
    row_dict = {}
    for line in lines[0+3:len(lines)-1]:
        fields = line.split()
        #print fields
        rank = fields[0]
        row_dict[rank] = fields[1:]
    return [(col_list[1:],row_dict)]

def cat_calltypes(list, calltype):
    fn = lambda x: calltype+'_'+x
    return map(fn,list)

def parse_section_AGG_TIME(lines):
    #           0                    1          2       3       4
    col_list = 'Call                 Site       Time    App-pct MPI-pct'.split()
               #Waitall               145       9.42    0.00   99.89
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        row_dict = {}
        fields = line.split()
        #print fields
        calltype = fields[0]
        col_names = cat_calltypes(col_list[2:5],calltype)
        row_dict["*"] = fields[2:5]
        set_list.append((col_names,row_dict))
    return set_list

def parse_section_AGG_SIZE(lines):
    #           0                    1         2          3           4
    col_list = 'Call                 Site      Count      Total       Avrg  Sent-pct'.split()
               #Allgather               3          1          4          4 100.00
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        row_dict = {}
        fields = line.split()
        #print fields
        calltype = fields[0]
        col_names = cat_calltypes(col_list[2:4],calltype)
        row_dict["*"] = fields[2:4]
        set_list.append((col_names,row_dict))
    return set_list

def parse_section_AGG_COLLECTIVE_TIME(lines):

    #           0                    1                      2                     3
    col_list = 'Call                 MPI-Time-pct           Comm-Size             Data-Size'.split()
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        row_dict = {}
        f = line.split()
        #0                        1              2  3       4           5 6        7
        #Allgather                0.0123         16 -       31          0 -        7
        fields = [f[0], f[1], ''.join(f[2:5]), ''.join(f[5:8])]
        #print fields
        #0                        1              2                      3
        #Allgather                0.0123         16-31                  0-7
        calltype = '_'.join([fields[0],fields[2],fields[3]])
        col_names = cat_calltypes(col_list[1:2],calltype)
        row_dict["*"] = fields[1:2]
        set_list.append((col_names,row_dict))
    return set_list

def parse_section_AGG_P2P_SENT(lines):

    #           0                    1                      2                     3
    col_list = 'Call                 MPI-Sent-pct           Comm-Size             Data-Size'.split()
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        row_dict = {}
        f = line.split()
        #0                        1              2  3       4           5 6        7
        #Allgather                0.0123         16 -       31          0 -        7
        fields = [f[0], f[1], ''.join(f[2:5]), ''.join(f[5:8])]
        #print fields
        #0                        1              2                      3
        #Allgather                0.0123         16-31                  0-7
        calltype = '_'.join([fields[0],fields[2],fields[3]])
        col_names = cat_calltypes(col_list[1:2],calltype)
        row_dict["*"] = fields[1:2]
        set_list.append((col_names,row_dict))
    return set_list

def parse_section_AGG_P2P_STAT(lines):

    #           0        1          2           3
    col_list = 'Src-Rank Dest-Rank  Total-Size  Total-Time'.split()
                #0        1         4           0.002
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        row_dict = {}
        f = line.split()
        #0        1         4      0.002
        #1        2         4      0.005
        #print fields
        set_list.append(f)
    return (col_list,set_list)

def parse_section_AGG_P2P_STAT_PLUS_COUNT(lines):

    #           0        1          2           3
    col_list = 'Src-Rank Dest-Rank Total-Count Total-Size Total-Time'.split()
               #       0         1           1          4      0.005
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        row_dict = {}
        f = line.split()
        #       0         1           1          4      0.005
        #       1         2           1          4      0.004
        #print fields
        set_list.append(f)
    return (col_list,set_list)

def parse_section_CALLSITE_TIME_STAT(lines):

    #          0                  1    2     3          4       5         6     7         8
    col_list = 'Name              Site Rank  Count      Max     Mean      Min   App-pct   MPI-pct'.split()
               #Name              Site Rank  Count      Max     Mean      Min   App%      MPI%
               #Allgather            3    0      1     87.6     87.6     87.6   0.00      0.02
    col_dict = {}
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        if line == '': continue
        fields = line.split()
        #print fields
        calltype = fields[0]
        col_names = cat_calltypes([col_list[3],col_list[8]],calltype)
        col_string = ",".join(col_names)
        if col_string not in col_dict:
            col_dict[col_string] = {}
        rank = fields[2]
        col_dict[col_string][rank] = [fields[3],fields[8]]

    for col_string in col_dict.keys():
        #recover col_names list from comma separated col_names string
        col_names =  col_string.split(',')
        set_list.append((col_names,col_dict[col_string]))

    return set_list

def parse_section_CALLSITE_TIME_STAT_PLUS_TIME(lines):

    #          0                  1    2     3          4       5         6     7         8       9
    col_list = 'Name              Site Rank  Count      Max     Mean      Min   App-pct   MPI-pct Time'.split()
               #Name              Site Rank  Count      Max     Mean      Min   App%   MPI%       Time
               #Recv               101    0      1    0.318    0.318    0.318  91.12  99.38      0.318
    col_dict = {}
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        if line == '': continue
        fields = line.split()
        #print fields
        calltype = fields[0]
        col_names = cat_calltypes([col_list[3],col_list[8],col_list[9]],calltype)
        col_string = ",".join(col_names)
        if col_string not in col_dict:
            col_dict[col_string] = {}
        rank = fields[2]
        col_dict[col_string][rank] = [fields[3],fields[8],fields[9]]

    for col_string in col_dict.keys():
        #recover col_names list from comma separated col_names string
        col_names =  col_string.split(',')
        set_list.append((col_names,col_dict[col_string]))

    return set_list

def parse_section_CALLSITE_SENT_STAT(lines):

    #          0                  1    2      3           4        5          6         7
    col_list = 'Name              Site Rank   Count       Max      Mean       Min       Sum'.split()
               #Name              Site Rank   Count       Max      Mean       Min       Sum
               #Allgather            3    0       1         4         4         4         4

    col_dict = {}
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        if line == '': continue
        fields = line.split()
        #print fields
        calltype = fields[0]
        col_names = cat_calltypes([col_list[3],col_list[7]],calltype)
        col_string = ",".join(col_names)
        if col_string not in col_dict:
            col_dict[col_string] = {}
        rank = fields[2]
        col_dict[col_string][rank] = [fields[3],fields[7]]

    for col_string in col_dict.keys():
        #recover col_names list from comma separated col_names string
        col_names =  col_string.split(',')
        set_list.append((col_names,col_dict[col_string]))

    return set_list

def parse_section_CALLSITE_SENT_STAT_PLUS_TIME(lines):

    #          0                  1    2      3           4        5          6         7         8
    col_list = 'Name              Site Rank   Count       Max      Mean       Min       Sum       Time'.split()
               #Name              Site Rank   Count       Max      Mean       Min       Sum       Time
               #Send               111    0       1    4.0000    4.0000    4.0000    4.0000      0.002

    col_dict = {}
    set_list = []
    for line in lines[0+3:len(lines)-1]:
        if line == '': continue
        fields = line.split()
        #print fields
        calltype = fields[0]
        col_names = cat_calltypes([col_list[3],col_list[7],col_list[8]],calltype)
        col_string = ",".join(col_names)
        if col_string not in col_dict:
            col_dict[col_string] = {}
        rank = fields[2]
        col_dict[col_string][rank] = [fields[3],fields[7],fields[8]]

    for col_string in col_dict.keys():
        #recover col_names list from comma separated col_names string
        col_names =  col_string.split(',')
        set_list.append((col_names,col_dict[col_string]))

    return set_list

sdict = {
    'MPI_TIME' : {
        'name' : '@--- MPI Time (seconds) ---------------------------------------------------',
        'cols' : ['AppTime', 'MPITime', 'MPI%'],
        'fn'   : parse_section_MPI_TIME,
    },
#    'AGG_TIME' : {
#        'name' : '@--- Aggregate Time (top twenty, descending, milliseconds) ----------------',
#        'cols' : ['Call_Time', 'Call_App%', 'Call_MPI%'],
#        'fn'   : parse_section_AGG_TIME,
#    },
#    'AGG_SIZE' : {
#        'name' : '@--- Aggregate Sent Message Size (top twenty, descending, bytes) ----------',
#        'cols' :['Call_Count', 'Call_Total'],
#        'fn'   : parse_section_AGG_SIZE,
#    },
    'AGG_COLLECTIVE_TIME' : {
        'name' :'@--- Aggregate Collective Time (top twenty, descending) -------------------',
        'cols' :['Call_Comm-Size_Data-Size'],
        'fn'   : parse_section_AGG_COLLECTIVE_TIME,
    },
    'AGG_P2P_SENT' : {
        'name' :'@--- Aggregate Point-To-Point Sent (top twenty, descending) ---------------',
        'cols' :['Call_Comm-Size_Data-Size'],
        'fn'   : parse_section_AGG_P2P_SENT,
    },
    'AGG_P2P_STAT' : {
        'name' :'@--- Aggregate Point-To-Point Stats (bytes, milliseconds) -----------------',
        'cols' :['Src-Rank_Dest-Rank_Total-Size_Total-Time'],
        'fn'   : parse_section_AGG_P2P_STAT,
    },
    'AGG_P2P_STAT_PLUS_COUNT' : {
        'name' :'@--- Aggregate Point-To-Point Stats (count, bytes, milliseconds) ----------',
        'cols' :['Src-Rank_Dest-Rank_Total-Count_Total-Size_Total-Time'],
        'fn'   : parse_section_AGG_P2P_STAT_PLUS_COUNT,
    },
    'CALLSITE_TIME_STAT' : {
        'name' :'@--- Callsite Time statistics (all, milliseconds):',
        'cols' :['Name_Count, Name_MPI%'],
        'fn'   : parse_section_CALLSITE_TIME_STAT,
    },
    'CALLSITE_TIME_STAT_PLUS_TIME' : {
        'name' :'@--- Callsite Time statistics (all, milliseconds, with time):',
        'cols' :['Name_Count, Name_MPI%, Name_Time'],
        'fn'   : parse_section_CALLSITE_TIME_STAT_PLUS_TIME,
    },
    'CALLSITE_SENT_STAT' : {
        'name' :'@--- Callsite Message Sent statistics (all, sent bytes) -------------------',
        'cols' :['Name_Count, Name_Sum'],
        'fn'   : parse_section_CALLSITE_SENT_STAT,
    },
    'CALLSITE_SENT_STAT_PLUS_TIME' : {
        'name' :'@--- Callsite Message Sent statistics (all, sent bytes, with time) --------',
        'cols' :['Name_Count, Name_Sum, Name_Time'],
        'fn'   : parse_section_CALLSITE_SENT_STAT_PLUS_TIME,
    },
    'END_OF_REPORT' : {
        'name' :'@--- End of Report --------------------------------------------------------',
        'cols' :[],
    }
}


#
# We really should be using exceptions here -pjm
#
def p2p_print_csv(csv,header_list,p2p_output_csv,verbose):
    if verbose:
        print "output : {0}".format(p2p_output_csv)
    with open(p2p_output_csv, 'w') as out_file:
        out_file.write("{0}\n".format(",".join(header_list)))
        for p2p_data in csv:
            out_file.write("{0}\n".format(",".join(p2p_data)))
        out_file.flush()
        os.fsync(out_file.fileno())

def print_csv(csv,rank_list,header_list,output_csv,verbose):
    if verbose:
        print "output : {0}".format(output_csv)
    with open(output_csv, 'w') as out_file:
        out_file.write("Rank,{0}\n".format(",".join(header_list)))
        for r in rank_list:
            if r == '*':
                #Print "AllRanks" instead of "*"
                out_file.write("{0},{1}\n".format("AllRanks",",".join(csv[r])))
            # FIXME 10-04-2016(IVO) disabling
            # else:
            # out_file.write("{0},{1}\n".format(r,",".join(csv[r])))
        out_file.flush()
        os.fsync(out_file.fileno())

#
# We should be checking the filename format here -pjm
#
def get_mpip_name(file_name):
    #file_name is foo.bar.xyz.mpiP
    split_txt = file_name.split('.')
    index = len(split_txt)-1
    file_name = '.'.join(split_txt[0:index])
    return file_name

def usage():
    return '''The script converts the detailed textual output of mpiP into CSV format'''

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=usage())
    p.add_argument('-f','--force', action='store_true',
                   help='Overwrite output .csv file, if one exists')
    p.add_argument('-v','--verbose', action='store_true',
                   help='Display information about input and output files as they are processed')
    p.add_argument('mpipfile',
                   help='mpiP output file to be processed')
    args = p.parse_args()

    #Check is input .mpiP file is present
    # stop using isfile! use exceptions! -pjm
    input_file = args.mpipfile
    if not os.path.isfile(input_file):
        if args.verbose:
            print "{0}: {1} not found, exiting.".format(__file__,input_file)
        sys.exit(1)

    #Count ranks in in mpiP file
    RANK_LINE = '@ MPI Task Assignment      : '
    RANK_LL   = len(RANK_LINE)
    nranks = 0

    lines = []
    range_dict = {}

#
# We really should be using exceptions here -pjm
#
# Do not use file as a var name, it is a builtin! -pjm
#
    with open(input_file, 'r') as mpip_file:

        current_section = ''
        current_line = 0
        lines_set = set(names())
        tag_dict = revnames()
        lines = mpip_file.read().splitlines()
        for _line in lines:
            #Trim all '@--- XYZ (...): ---' lines to the ')' character
            limit = _line.find(')')
#
# Not supposed to use is with literals -pjm
#
            if limit == -1: line = _line
            else: line = _line[:limit]

            if line[:RANK_LL] == RANK_LINE:
                nranks +=1
            elif line in lines_set:
                if current_section != '':
                    range_dict[current_section]["end"] = current_line
                next_section = tag_dict[line]
                range_dict[next_section] = {"begin":current_line, "end":0}
                current_section = next_section
            current_line += 1

    if args.verbose:
        print "Found {0} Tasks(Ranks)".format(nranks)

    #Parse Data from .mpiP file
    set_list = []
    p2p_data = ()
    for tag,range_ in range_dict.items():
        begin,end = (range_["begin"],range_["end"])
        if args.verbose:
            print "{0} :({1},{2})".format(tag,begin,end)
        if 'fn' in sdict[tag]:
            if args.verbose:
                print "parsing : {0}".format(tag)
            #data is a tuple of (column_names, dict[rank] =[corresponding row elems])
            #     or a tuple of (column_names, [list of corresponding row elems])
            data = sdict[tag]['fn'](lines[begin:end])

            #Point 2 Point stats are stored in sections with 1 of two formats
            #listed below. Only one of these sections will exist in .mpiP file
            if tag == 'AGG_P2P_STAT' or tag == 'AGG_P2P_STAT_PLUS_COUNT':
                p2p_data = data
            else:
                set_list.extend(data)

    #Create rank_list [ *, 0, ..., nranks]
    rank_list = ['*']
    rank_list.extend(map(lambda x: str(x),range(0,nranks)))

    #Pring the P2P STATS data
    if p2p_data:
        p2p_header, p2p_list = p2p_data
        p2p_output_csv = get_mpip_name(input_file) + '.p2p.csv'
        if (os.path.isfile(p2p_output_csv)):
            if args.force:
                if args.verbose:
                    print "{0}: {1} already exists, overwriting.".format(__file__,p2p_output_csv)
                p2p_print_csv(p2p_list,p2p_header,p2p_output_csv,args.verbose)
            else:
                print "{0}: {1} already exists, skipping.".format(__file__,p2p_output_csv)
        else:
            p2p_print_csv(p2p_list,p2p_header,p2p_output_csv,args.verbose)

    #Start Formatting CSV Data Structures for Output
    csv_header = []
    csv_dict = {}
    for r in rank_list:
        csv_dict[r] = []

#
# Do not use set as a var name, it is a builtin! -pjm
#
    for mpip_set in set_list:
        header_list, row_dict = mpip_set
        ncols = len(header_list)
        csv_header.extend(header_list)
        for rank in rank_list:
            row = csv_dict[rank]
            if rank in row_dict:
                row.extend(row_dict[rank])
            else:
                row.extend(map(lambda x: '', range(0,ncols)))

    # Write to Output File
    # Stop if output csv file already exists
    # stop using isfile! use exceptions! -pjm
    output_csv = get_mpip_name(input_file) + '.mpiP.csv'
    if (os.path.isfile(output_csv)):
        if args.force:
            if args.verbose:
                print "{0}: {1} already exists, overwriting.".format(__file__,output_csv)
            print_csv(csv_dict,rank_list,csv_header,output_csv,args.verbose)
        else:
            print "{0}: {1} already exists, skipping.".format(__file__,output_csv)
    else:
        print_csv(csv_dict,rank_list,csv_header,output_csv,args.verbose)

    sys.exit(0)

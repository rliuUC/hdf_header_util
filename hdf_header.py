#! /usr/bin/env python3
import os
import argparse
import h5py
from glob import glob
from prettytable import PrettyTable


def read_header_entry(filename,hdr_key,decode=False):
    '''
    Queries HDF /header group for a certain attribute (aka 'header keyword') and return result (value)

    :param filename: HDF file name
    :param hdr_key: header keyword to query
        :param decode: decode native byte format to ascii
    :return:
    '''
    with h5py.File(filename, 'r', libver='latest') as h5f:
        value = h5f['header'].attrs.get(hdr_key)
        if decode:
            value = value.decode('utf8')

    return value


def read_header(filename,decode=False):
    '''
    :param filename: HDF file name
    :param decode: decode native byte format to ascii
    :return:
    '''
    with h5py.File(filename, 'r', libver='latest') as h5f:
        header = dict(h5f['header'].attrs.items())
        if decode:
            for key in header.keys():
                try:
                    header[key] = header[key].decode('utf8')
                except:
                    pass

    return header


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Script to read and print hdf headers in MAROON-X files.'
    )

    p_input  = parser.add_argument_group('Input')
    p_output = parser.add_argument_group('Output')

    p_input.add_argument(
            '-dd', '--data_directory',
            help="Directory for hdf input files.",
            type=str, default="", required=False
    )

    p_input.add_argument(
            '-f', '--filename',
            help="Name of file(s), e.g. 20200526T070224Z_SOOOE_b_0600.hdf or 20*_SOOOE_?_*.hdf",
            type=str, default="", required=True
    )

    p_input.add_argument(
            '-k', '--header_keywords',
            help="Header keywords or part of keyword to query. If omitted, print complete header of first file.",
            nargs='*',type=str, default="", required=False
    )

    p_input.add_argument(
            '-ff', '--filter',
            help="Filter for specific keyword value pair. Format: keyword=value, e.g. TARGETNAME='Barnard Star'",
            type=str, default="", required=False
    )

    p_input.add_argument(
            '-of', '--outfile',
            help="Name of output file containing all the filenames that pass the filtering (e.g. as input for SERVAL).",
            type=str, default="", required=False
    )

    args = parser.parse_args()

    if args.outfile and not args.filter:
        parser.error("--outfile requires --filter.")

    if args.filter and args.header_keywords:
        parser.error("--filter and --header_keywords cannot be used " + "simultaneously.")

    files = glob(os.path.join(args.data_directory,args.filename))

    if args.filter:
        target_key   = args.filter.split('=')[0]
        target_value = args.filter.split('=')[1]

        x = []

        for file in files:
            header = read_header(file,decode=True)
            for key in header.keys():
                if target_key in key or target_key.upper() in key:
                    if target_value in header[key]:
                        x.append(os.path.abspath(file))

        if not args.outfile:
            if len(x) > 0:
                for f in x:
                    print(f)
            else:
                print("No matching files found")
        else:
            if len(x) > 0:
                fout = open(args.outfile, "w")
                for f in x:
                    fout.write(f + '\n')
            else:
                print("No matching files found")


    elif not args.header_keywords:
        print(f"\n\nDisplaying full header {files[0].split('/')[files[0].count('/')]}\n\n")
        header = read_header(files[0],decode=True)
        x = PrettyTable()
        x.field_names = ["Header Keyword","Value"]
        for key in header.keys():
            x.add_row([key, header[key]])
        print(x)

    else:
        matched_keys = []
        matched_values = []
        headers = []

        for i,file in enumerate(files):
            header = read_header(file,decode=True)
            headers.append(header)
            for header_keyword in args.header_keywords:
                for key in header.keys():
                    if header_keyword in key or header_keyword.upper() in key:
                        if not key in matched_keys:
                            matched_keys.append(key)

        matched_keys = sorted(matched_keys)

        for i,file in enumerate(files):
            header = headers[i]
            cur_file_matched_values = [file.split('/')[-1]]

            for final_key in matched_keys:
                try:
                    cur_file_matched_values.append(header[final_key])
                except:
                    cur_file_matched_values.append("")

            matched_values.append(cur_file_matched_values)

        if not matched_keys:
            print(
                "\nNo matching entries found for header keyword",
                end=("s: " if (len(args.header_keywords) > 1) else ": ")
            )
            for i in range(len(args.header_keywords)):
                print(
                    args.header_keywords[i],
                    end=(", " if (i != len(args.header_keywords) - 1) else "\n\n")
                )

        else:
            x = PrettyTable()
            x.field_names = ['Filename'] + matched_keys
            for cur_file_matched_values in matched_values:
                x.add_row(cur_file_matched_values)
            print(x)

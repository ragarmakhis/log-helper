import argparse
import sys

from utils.read_write_xml import get_bin_list, write_xml
from log_helper import get_xml_items, WorkArguments


def get_arguments() -> WorkArguments:
    p = argparse.ArgumentParser()
    p.add_argument('file')
    p.add_argument('-b', '--bin', action='store_true', default=False)
    p.add_argument('-n', '--next_day', action='store_true', default=False)
    p.add_argument('-p', '--prev_day', action='store_true', default=False)
    p.add_argument('-nr', '--rename', action='store_false', default=True)
    p.add_argument('-m', '--merge', action='store_true', default=False)
    p.add_argument('-B', '--batch', action='store_true', default=False)
    p.add_argument('--testing', action='store_true', default=False)

    return WorkArguments(**vars(p.parse_args(sys.argv[1:])))


def main():
    arguments = get_arguments()
    bin_list = get_bin_list(arguments)
    xml_items = get_xml_items(bin_list, arguments)
    write_xml(xml_items)

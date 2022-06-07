from typing import List

from lxml import etree
from lxml.etree import _Element

from log_helper.config import OUTPUT_PATH
from log_helper.log_helper import WorkArguments


def get_bin_list(arguments: WorkArguments) -> List[_Element]:
    tree = etree.parse(arguments.file)
    root = tree.getroot()
    return root.findall('bin') if arguments.batch else [root]


def write_xml(items: List) -> None:
    xml = etree.Element('xmeml', version="5")
    for item in items:
        for node in item:
            xml.append(node.create_node())
    xml_file = etree.ElementTree(xml)
    xml_file.write(OUTPUT_PATH, pretty_print=True, xml_declaration=True,
                   encoding="utf-8", doctype="<!DOCTYPE xmeml>")

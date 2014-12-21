# Task:
# export xml with name= x=, y=, width=, height= for all groups and layers
#   layers in groups have relative coordinates to parent
#   check integrity with jar parser
#
# export all layers as png
#   don't export text_ node_
#   handle on unsupported characters in name
#   handle empty layers
#
# think of additional layer types to put into psd
#   info_, etc.

class bcolors:
    """ Colorized output with print """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'  # end coloring

import re
psd_re = re.compile('^.+\.psd$')
valid_name = re.compile('^\w+$')  # \w is [a-zA-z0-9_]

png_noexport=[
        re.compile('^noexport_\w+'),
        re.compile('^node_\w+'),
        re.compile('^text_\w+'),
        re.compile('^init_\w+'),
        ]

xml_noexport=[
        re.compile('^noexport_\w+'),
        ]

import xml.etree.ElementTree as ET
from xml.dom import minidom
import psd_tools
import os

def main():
    psd_filepath='../test2.psd'
    PsdParser().parse(psd_filepath)


class PsdParser(object):
    def __init__(self):
        self.__psd = None
        self.__psd_name = None
        self.__xml_root = None
        self.__xml_target = None
        self.__error_flag = False

    def parse(self, psd_filepath):
        psd_filename= os.path.basename(psd_filepath)
        if not psd_re.match(psd_filename):
            print("'"+ psd_filename +"': not a psd file")
            return
        # all self vars must be reinited
        self.__psd = psd_tools.PSDImage.load(psd_filepath)
        self.__psd_name = os.path.splitext(os.path.basename(psd_filepath))[0]
        self.__psd_path = os.path.realpath(os.path.dirname(psd_filepath))
        # print  "----------------------------------------------------"
        print "Path: "+ self.__psd_path
        print "----------------------------------------------------"
        self.__xml_root=ET.Element('layers')
        self.__xml_target=self.__xml_root
        self.__error_flag = False
        # parse
        self.__parse_layers(self.__psd.layers)
        self.__save_xml()
        if self.__error_flag:
            print bcolors.FAIL + "---------------- PARSED WITH ERRORS ----------------" + bcolors.ENDC
        else:
            print bcolors.OKGREEN + "---------------- PARSED SUCCESSFULLY ---------------" + bcolors.ENDC

    def __parse_layers(self, group, parent_x=0, parent_y=0):
        for layer in reversed(group):
            if not self.__is_valid(layer):
                print(bcolors.FAIL + 'Wrong chars in name: \t\t\t'+self.__psd_name+"_"+layer.name + bcolors.ENDC)
                self.__error_flag = True
                continue  # skip invalid named layers
            latest_xml_element = self.__append_to_xml(layer, parent_x, parent_y)
            if self.__is_group(layer):
                xml_target_backup = self.__xml_target
                self.__xml_target = latest_xml_element
                self.__parse_layers(layer.layers, layer.bbox[0], layer.bbox[1])
                self.__xml_target = xml_target_backup
            else:
                self.__export_to_png(layer)

    def __append_to_xml(self, layer, parent_x, parent_y):
        for noexport in xml_noexport:
            if noexport.match(layer.name):
                return
        element_type = 'group' if self.__is_group(layer) else 'layer'
        element = ET.Element(element_type,
            {
                'name':layer.name,
                'x':str(layer.bbox[0] - parent_x),
                'y':str(layer.bbox[1] - parent_y),
                'width':str(layer.bbox[2]-layer.bbox[0]),
                'height':str(layer.bbox[3]-layer.bbox[1]),
            })
        self.__xml_target.append(element)
        return element

    def __save_xml(self):
        rough_str = ET.tostring(self.__xml_root)
        xml_node = minidom.parseString(rough_str)
        # print xml_node.toprettyxml(indent="\t")
        xml_filepath = os.path.join(self.__psd_path, self.__psd_name+'.xml')
        with open(xml_filepath, "w") as file:
            # xml_node.writexml(file, addindent="\t", newl="\n")
            print "Saving xml: " + xml_filepath

    def __export_to_png(self, layer):
        for noexport in png_noexport:
            if noexport.match(layer.name):
                # print('Noexport: \t\t'+self.__psd_name+"_"+layer.name)
                return
        if not self.__has_pixels(layer):
            print(bcolors.FAIL + 'Empty layer: \t\t' + layer.name + bcolors.ENDC)
            self.__error_flag = True
            return
        png_filename = self.__psd_name + "_" +layer.name + ".png"
        png_path = os.path.join(self.__psd_path, self.__psd_name)
        if not os.path.exists(png_path):
            os.mkdir(png_path)
        # image = layer.as_PIL()
        # image.save(os.path.join(png_path , png_filename))
        print('Saving: \t\t' + png_filename)

    def __is_group(self, layer):
        return hasattr(layer,'layers')

    def __has_pixels(self, layer):
        return layer.bbox[0]!=layer.bbox[2] and layer.bbox[1]!=layer.bbox[3]

    def __is_valid(self, layer):
        return bool(valid_name.match(layer.name))


if __name__ == '__main__':
    main()


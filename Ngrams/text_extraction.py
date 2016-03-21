import xml.etree.ElementTree as ET
import os

f = open('all_texts_2.in', 'w')

directory = 'D:/CSC/ShlyapaBot/_Lib.rus.ec - Официальная/lib.rus.ec./fb2-030560-060423'
files = os.listdir(directory)

count = 1
for file_name in files:
    file_path = directory + "/" + file_name
    print("Step #" + str(count) + ", processing " + file_path)

    try:
        tree = ET.parse(file_path)
    except ET.ParseError:
        print("  not well-formed")
    else:
        root = tree.getroot()
        for child in root[1]:
            if child.tag != '{http://www.gribuser.ru/xml/fictionbook/2.0}section':
                continue
            for child2 in child:
                if child2.text != None:
                    try:
                        f.write(child2.text)
                        f.write('\n')
                    except UnicodeEncodeError:
                        print("  problems with encoding")

    finally:
        count += 1
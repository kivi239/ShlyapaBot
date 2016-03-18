import xml.etree.ElementTree as ET
tree = ET.parse('D:/CSC/ShlyapaBot/_Lib.rus.ec - Официальная/lib.rus.ec./fb2-000024-030559/1005.fb2')
root = tree.getroot()

print(root[1].tag)

f = open('all_texts.in', 'w')

for child in root[1][1]:
    f.write(child.text)
    f.write('\n')

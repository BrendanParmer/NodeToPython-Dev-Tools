from bs4 import BeautifulSoup
from threading import Thread, Lock
import os
import re
from typing import Dict, List, NamedTuple, Tuple

import types_utils

class NTPNodeSetting(NamedTuple):
    name_: str
    type_: str

mutex = Lock()
nodes_dict : Dict[str, Dict[NTPNodeSetting, List[Tuple[int, int]]]] = {}

def process_node(node: str, section, version: Tuple[int, int]):
    global nodes_dict
    with mutex:
        if node not in nodes_dict:
            nodes_dict[node] = {}

    attrs = section.find_all("dl", class_="py attribute")

    for attr in attrs:
        name_section = attr.find(["code", "span"], class_="sig-name descname")
        
        if not name_section:
            raise ValueError(f"{version} {node}: Couldn't find name section in\n\t{section}")
        name = name_section.text
        
        type_section = attr.find("dd", class_="field-odd")
        if not type_section:
            raise ValueError(f"{version} {node}.{name}: Couldn't find type section in\n\t{section}")
        type_text = type_section.text

        ntp_type = types_utils.get_NTP_type(type_text)
        if ntp_type == "":
            raise ValueError(f"{version} {node}.{name}: Unexpected type string {type_text}")

        ntp_setting = NTPNodeSetting(name, ntp_type)
        with mutex:
            if ntp_setting not in nodes_dict[node]:
                nodes_dict[node][ntp_setting] = [version]
            else:
                nodes_dict[node][ntp_setting].append(version)

def get_subclasses(current: str, parent: str, root_path: str, 
                   version: Tuple[int, int]) -> list[str]:
    current_path = os.path.join(root_path, f"bpy.types.{current}.html")

    with open(current_path, "r") as current_file:
        current_html = current_file.read()

    soup = BeautifulSoup(current_html, "html.parser")

    sections = soup.find_all(id=f"{current.lower()}-{parent.lower()}")
    if not sections:
        raise ValueError(f"{version} {current}: Couldn't find main section")

    section = sections[0]
    paragraphs = section.find_all("p")
    if len(paragraphs) < 2:
        raise ValueError(f"{version} {current}: Couldn't find subclass section")

    subclasses_paragraph = paragraphs[1]
    if not subclasses_paragraph.text.strip().startswith("subclasses —"):
        # No subclasses for this type
        process_node(current, section, version)
        return

    subclass_anchors = subclasses_paragraph.find_all("a")
    if not subclass_anchors:
        raise ValueError(f"{version} {current} No anchors in subclasses paragraph")

    subclass_types = [anchor.get("title") for anchor in subclass_anchors]
    threads: List[Thread] = []
    for type in subclass_types:
        if not type:
            raise ValueError(f"{version} {current} Type was invalid")
        is_matching = re.match(r"bpy\.types\.(.*)", type)
        if not is_matching:
            raise ValueError(f"{version} {current}: Type {type} was not of the form \"bpy.types.x\"")
        pure_type = is_matching.group(1)
        if (pure_type == "TextureNode"):
            # unsupported
            continue

        thread = Thread(target=get_subclasses, args=(pure_type, current, root_path, version))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

def process_bpy_version(version: Tuple[int, int]) -> None:
    print(f"Processing version {version[0]}.{version[1]}")

    current = "NodeInternal"
    parent = "Node"

    root_path = os.path.join(bpy_docs_path, 
                             f"{version[0]}.{version[1]}/"
                             f"blender_python_reference_"
                             f"{version[0]}_{version[1]}")

    get_subclasses(current, parent, root_path, version)

if __name__ == "__main__":
    current_path = os.path.dirname(os.path.realpath(__file__))
    dev_tools_path = os.path.dirname(current_path)
    bpy_docs_path = os.path.join(dev_tools_path, "bpy_docs")

    versions = [(3, i) for i in range(0, 7)]
    versions += [(4, i) for i in range(0, 2)]

    for version in versions:
        process_bpy_version(version)

    #used for exclusive max version
    versions.append((4, 2))

    sorted_nodes = dict(sorted(nodes_dict.items()))

    output_dir_path = os.path.join(current_path, "output")
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)

    output_filepath = os.path.join(output_dir_path, "node_settings.py")



    with open(output_filepath, 'w') as file:
        print(f"Writing settings to {output_filepath}")

        file.write("from utils import ST, NTPNodeSetting\n\n")
        file.write("node_settings : dict[str, list[NTPNodeSetting]] = {\n")
        
        for node, attr_dict in sorted_nodes.items():
            file.write(f"\t\'{node}\' : [\n")

            for attr, attr_versions in attr_dict.items():
                min_version = min(attr_versions)

                inclusive_max_version = max(attr_versions)
                inclusive_max_index = versions.index(inclusive_max_version)
                exclusive_max_version = versions[inclusive_max_index + 1]

                min_version_str = f"min_version=({min_version[0]}, {min_version[1]}, 0)"
                max_version_str = f"max_version=({exclusive_max_version[0]}, {exclusive_max_version[1]}, 0)"
                file.write(f"\t\tNTPNodeSetting(\"{attr.name_}\", {attr.type_}, "
                           f"{min_version_str}, {max_version_str}),\n")
            
            file.write("\t],\n\n")

        file.write("}")

        print("Successfully finished")
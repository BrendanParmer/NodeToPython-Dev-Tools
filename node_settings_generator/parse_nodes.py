import argparse
from bs4 import BeautifulSoup
from threading import Thread, Lock
import os
import re
import time
from typing import Dict, List, NamedTuple, Tuple
import urllib.request

import types_utils

class NTPNodeSetting(NamedTuple):
    name_: str
    type_: str

mutex = Lock()
log_mutex = Lock()
nodes_dict : Dict[str, Dict[NTPNodeSetting, List[Tuple[int, int]]]] = {}
types_dict : Dict[str, set[str]] = {}
log_file = None

NTP_MIN_VERSION = (3, 0)

def process_attr(attr, section, node: str, version: Tuple[int, int]) -> None:
    name_section = attr.find(["code", "span"], class_="sig-name descname")
    
    if not name_section:
        raise ValueError(f"{version} {node}: Couldn't find name section in\n\t{section}")
    name = name_section.text
    
    type_section = attr.find("dd", class_="field-odd")
    if not type_section:
        raise ValueError(f"{version} {node}.{name}: Couldn't find type section in\n\t{section}")
    type_text = type_section.text

    with mutex:
        first_word = type_text.split()[0]
        if first_word not in types_dict:
            types_dict[first_word] = {type_text}
        else:
            types_dict[first_word].add(type_text)

    ntp_type = types_utils.get_NTP_type(type_text)
    if ntp_type == "":
        raise ValueError(f"{version} {node}.{name}: Unexpected type string {type_text}")
    elif ntp_type is None:
        # Read-only attribute, don't add to attribute list
        with log_mutex:
            log_file.write(f"WARNING: {version} {node}.{name}'s type is being ignored:\n\t{type_text.strip()}\n")
        return

    ntp_setting = NTPNodeSetting(name, ntp_type)
    with mutex:
        if ntp_setting not in nodes_dict[node]:
            nodes_dict[node][ntp_setting] = [version]
        else:
            nodes_dict[node][ntp_setting].append(version)

def process_node(node: str, section, version: Tuple[int, int]):
    global nodes_dict
    with mutex:
        if node not in nodes_dict:
            nodes_dict[node] = {}

    attrs = section.find_all("dl", class_="py attribute")

    for attr in attrs:
        process_attr(attr, section, node, version)

    datas = section.find_all("dl", class_="py data")
    for data in datas:
        process_attr(data, section, node, version)

def download_file(filepath: str, version: Tuple[int, int], local_path: str) -> bool:
    file_url = f"https://docs.blender.org/api/{version[0]}.{version[1]}/{filepath}"

    headers_ = {'User-Agent': 'Mozilla/5.0'}

    req = urllib.request.Request(file_url, headers=headers_)

    if not os.path.exists(os.path.dirname(local_path)):
        os.makedirs(os.path.dirname(local_path))

    while True:
        try:
            with urllib.request.urlopen(req) as response:
                with open(local_path, 'wb') as file:
                    file.write(response.read())
                    break
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(1.0)
            else:
                raise

    print(f"Downloaded {file_url} to {local_path}")
    return True


def get_subclasses(current: str, parent: str, root_path: str, 
                   version: Tuple[int, int]) -> list[str]:
    relative_path = f"bpy.types.{current}.html"
    current_path = os.path.join(root_path, relative_path)

    if not os.path.exists(current_path):
        download_file(relative_path, version, current_path)

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

def get_version_str(version: Tuple[int, int]) -> str:
    return f"{version[0]}.{version[1]}"

def process_bpy_version(version: Tuple[int, int]) -> None:
    print(f"Processing version {version[0]}.{version[1]}")

    current = "NodeInternal"
    parent = "Node"

    root_path = os.path.join(bpy_docs_path, 
                             f"{get_version_str(version)}/")

    get_subclasses(current, parent, root_path, version)

def generate_versions(max_version: Tuple[int, int]) -> List[Tuple[int, int]]:
    BLENDER_3_MAX_VERSION = 6

    versions = [(3, i) for i in range(0, BLENDER_3_MAX_VERSION + 1)]
    versions += [(4, i) for i in range(0, max_version[1] + 1)]
    
    return versions

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('max_major_version', type=int, 
                        help="Max major version (inclusive) of Blender to generate node settings for")
    parser.add_argument('max_minor_version', type=int, 
                        help="Max minor version (inclusive) of Blender to generate node settings for")
    args = parser.parse_args()

    current_path = os.path.dirname(os.path.realpath(__file__))
    dev_tools_path = os.path.dirname(current_path)
    bpy_docs_path = os.path.join(dev_tools_path, "bpy_docs")

    NTP_MAX_VERSION_INC = (args.max_major_version, args.max_minor_version)
    max_version_path = os.path.join(bpy_docs_path, f"{get_version_str(NTP_MAX_VERSION_INC)}")

    versions = generate_versions(NTP_MAX_VERSION_INC)

    output_dir_path = os.path.join(current_path, "output")
    if not os.path.exists(output_dir_path):
        os.makedirs(output_dir_path)

    log_filepath = os.path.join(output_dir_path, "log.txt")
    log_file = open(log_filepath, 'w')

    for version in versions:
        process_bpy_version(version)

    NTP_MAX_VERSION_EXC = (NTP_MAX_VERSION_INC[0], NTP_MAX_VERSION_INC[1] + 1)
    versions.append(NTP_MAX_VERSION_EXC)

    sorted_nodes = dict(sorted(nodes_dict.items()))

    output_filepath = os.path.join(output_dir_path, "node_settings.py")

    with open(output_filepath, 'w') as file:
        print(f"Writing settings to {output_filepath}")

        file.write("from .utils import ST, NTPNodeSetting\n\n")
        file.write("node_settings : dict[str, list[NTPNodeSetting]] = {\n")
        
        for node, attr_dict in sorted_nodes.items():
            file.write(f"\t\'{node}\' : [")

            attrs_exist = len(attr_dict.items()) > 0
            if attrs_exist:
                file.write("\n")

            sorted_attrs = dict(sorted(attr_dict.items()))
            for attr, attr_versions in sorted_attrs.items():
                attr_min_v = min(attr_versions)

                attr_max_v_inc = max(attr_versions)
                attr_max_v_inc_idx = versions.index(attr_max_v_inc)
                attr_max_v_exc = versions[attr_max_v_inc_idx + 1]

                min_version_str = ""
                if attr_min_v != NTP_MIN_VERSION:
                    min_version_str = f", min_version=({attr_min_v[0]}, {attr_min_v[1]}, 0)"

                max_version_str = ""
                if attr_max_v_exc != NTP_MAX_VERSION_EXC:
                    max_version_str = f", max_version=({attr_max_v_exc[0]}, {attr_max_v_exc[1]}, 0)"
                file.write(f"\t\tNTPNodeSetting(\"{attr.name_}\", {attr.type_}"
                           f"{min_version_str}{max_version_str}),\n")
            
            if attrs_exist:
                file.write("\t")
            file.write("],\n\n")

        file.write("}")

        print("Successfully finished")

    sorted_types = dict(sorted(types_dict.items()))
    log_file.write("\nTypes encountered:\n")
    for key, value in types_dict.items():
        log_file.write(f"{key}\n")
        for string in value:
            log_file.write(f"\t{string}\n")
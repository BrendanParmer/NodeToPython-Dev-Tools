import argparse
from bs4 import BeautifulSoup
from threading import Thread, Lock
import os
import re
import string
from typing import Dict, List, NamedTuple

class NTPNodeSetting(NamedTuple):
    name_: str
    type_: str

mutex = Lock()
nodes_dict : Dict[str, List[NTPNodeSetting]] = {}
i = 0

def process_node(node, section):
    global i
    global nodes_dict

    with mutex:
        print(f"{i}: Processing node {node}")
        i += 1

    attrs = section.find_all("dl", class_="py attribute")
    attr_list : List[NTPNodeSetting] = []
    for attr in attrs:
        name = attr.find("span", class_="sig-name descname").text
        
        type_text = attr.find("dd", class_="field-odd").text
        type = type_text.strip().split()[0]
        type = re.sub(r'[^A-Za-z\.]', '', type)

        attr_list.append(NTPNodeSetting(name, type))
    
    with mutex:
        nodes_dict[node] = attr_list

def get_subclasses(current: str, parent: str) -> list[str]:
    current_path = os.path.join(root_path, f"bpy.types.{current}.html")

    with open(current_path, "r") as current_file:
        current_html = current_file.read()

    soup = BeautifulSoup(current_html, "html.parser")

    sections = soup.find_all(id=f"{current.lower()}-{parent.lower()}")
    if not sections:
        raise ValueError(f"{current}: Couldn't find main section")

    section = sections[0]
    paragraphs = section.find_all("p")
    if len(paragraphs) < 2:
        raise ValueError(f"{current}: Couldn't find subclass section")

    subclasses_paragraph = paragraphs[1]
    if not subclasses_paragraph.text.strip().startswith("subclasses —"):
        # No subclasses for this type
        process_node(current, section)
        return

    subclass_anchors = subclasses_paragraph.find_all("a")
    if not subclass_anchors:
        raise ValueError(f"{current} No anchors in subclasses paragraph")

    subclass_types = [anchor.get("title") for anchor in subclass_anchors]
    threads: List[Thread] = []
    for type in subclass_types:
        if not type:
            raise ValueError(f"{current} Type was invalid")
        is_matching = re.match(r"bpy\.types\.(.*)", type)
        if not is_matching:
            raise ValueError(f"{current}: Type {type} was not of the form \"bpy.types.x\"")
        pure_type = is_matching.group(1)
        if (pure_type == "TextureNode"):
            # unsupported
            continue

        thread = Thread(target=get_subclasses, args=(pure_type, current))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto-generate node settings based on the bpy API documentation")
    parser.add_argument("site_path", help="Path to the downloaded website")
    args = parser.parse_args()

    root_path = os.path.abspath(args.site_path)

    current = "NodeInternal"
    parent = "Node"

    get_subclasses(current, parent)

    sorted_nodes = dict(sorted(nodes_dict.items()))
    for node, attr_list in sorted_nodes.items():
        print(node)
        for attr in attr_list:
            print(f"\t{attr.name_}: {attr.type_}")
        print("")
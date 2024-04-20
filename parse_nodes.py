import argparse
from bs4 import BeautifulSoup
import os
import re
import threading

def process_type(type: str):
    return

def get_subclasses(current: str, parent: str) -> list[str]:
    current_path = os.path.join(root_path, f"bpy.types.{current}.html")

    with open(current_path, "r") as current_file:
        current_html = current_file.read()

    soup = BeautifulSoup(current_html, "html.parser")

    section = soup.find_all(id=f"{current.lower()}-{parent.lower()}")
    if not section:
        raise ValueError(f"{current}: Couldn't find main section")

    paragraphs = section[0].find_all("p")
    if len(paragraphs) < 2:
        raise ValueError(f"{current}: Couldn't find subclass section")

    subclasses_paragraph = paragraphs[1]
    if not subclasses_paragraph.text.strip().startswith("subclasses —"):
        # No subclasses for this type
        process_type(current)
        return

    subclass_anchors = subclasses_paragraph.find_all("a")
    if not subclass_anchors:
        raise ValueError(f"{current} No anchors in subclasses paragraph")

    subclass_types = [anchor.get("title") for anchor in subclass_anchors]
    threads = []
    for type in subclass_types:
        if not type:
            raise ValueError(f"{current} Type was invalid")
        is_matching = re.match(r"bpy\.types\.(.*)", type)
        if not is_matching:
            raise ValueError(f"{current}: Type {type} was not of the form \"bpy.types.x\"")
        pure_type = is_matching.group(1)
        if (pure_type == "TextureNode"):
            # unsupported
            return

        print(pure_type)

        thread = threading.Thread(target=get_subclasses, args=(pure_type, current))
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
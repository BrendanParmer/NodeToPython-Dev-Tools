# NodeToPython-Dev-Tools
A repository hosting tools to automate and speed up some aspects of development for the Blender add-on [NodeToPython](https://github.com/BrendanParmer/NodeToPython).

## Node Settings Generator
(Instructions may need adjusted depending on your operating system, especially Windows)
1. Download the required `bpy` documentation from the Blender website by running
    ```
    python3 bpy_docs/download_docs.py
    ```

2. To create the node settings file, run
    ```
    python3 node_settings_generator/parse_nodes.py
    ```
# omega-to-openlabel

Converter utilities to export OmegaPRIME recordings into ASAM OpenLABEL format.

## Overview
- Input: OmegaPRIME recording (ASAM OpenDRIVE map + ASAM OSI moving objects/trajectories)
- Output: ASAM OpenLABEL file (JSON) with:
  - Coordinate systems (`scene`/odom and `vehicle-iso8855`)
  - Streams metadata needed for WebLABEL visualization
  - Static map objects uids (roads, sections, lanes) from OpenDRIVE
  - Dynamic objects (actors) with semantic types
  - Per-frame object data: acceleration, velocity, 3D cuboid bbox in `odom`
  - Relations:
    - `isNextTo` between adjacent lanes within a section
    - `isLocatedIn` intervals linking actors to lanes over time

## Dependencies
- Language: Python >= 3.9
- Libraries: `vcd`, `omega-prime`

## Project Structure
```
├── README.md
├── pyproject.toml              # Project metadata and entry points
├── LICENSE                     # CC BY-NC-SA 4.0 License file
├── assets/                     # Logos and images for documentation
├── weblabel_config/            # Misc files and readme for WebLABEL visualization
├── src/
│   └── omega_to_openlabel/
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       └── converter.py        # Main conversion logic
└── tests/                      # Unit and integration tests
```

## Installation
### 1. Prerequisites
Install vcd and omega-prime libraries:
```bash
pip install vcd 
pip install omega-prime
```
### 2. Install the package
To install the package in editable mode:
```bash
pip install -e .
```
## Usage

### Command Line Interface (CLI)
Once installed, you can use the `omega-to-openlabel` command directly:
```bash
omega-to-openlabel --input path/to/recording --output output.json --scene-name my_scene --add-relations
```

**Available Arguments:**
- `--input`, `-i`: Path to the OmegaPRIME recording.
- `--output`, `-o`: Path for the output OpenLABEL JSON file.
- `--scene-name`, `-s`: Name of the scene (default: `omega_scene`).
- `--add-relations`: Include lane relations and object-lane relations (default: `False`). Setting it to true makes the conversion process significantly slower, only set to true if the OpenLABEL files are going to be used as input for the scenario extraction tool of the SYNERGIES project.
- `--pretty`: Save the output JSON with indentation.
- `--verbose`, `-v`: Enable verbose logging.

### Python usage
You can also use the converter in your Python scripts:
```python
from omega_to_openlabel.converter import Omega2Openlabel, ConverterConfig
import omega_prime

# Load recording
recording = omega_prime.Recording.from_file("path/to/recording")

# Configure and run
config = ConverterConfig(
    openlabel_output_path="output.json",
    scene_name="my_scene",
    save_pretty=True
)
converter = Omega2Openlabel(recording, config)
converter.convert(add_relations=True)
```



## Acknowledgements
![synergies.svg](assets/synergies.svg)
This package is developed as part of the [SYNERGIES project](https://synergies-ccam.eu/) and is funded by the European Union. Views and opinions expressed are however those of the author(s) only and do not necessarily reflect those of the European Union or European Climate, Infrastructure and Environment Executive Agency (CINEA). Neither the European Union nor the granting authority can be held responsible for them.

![funded_by_eu.svg](assets/funded_by_eu.svg)

## License  
[![CC BY-NC-SA 4.0][cc-by-nc-sa-shield]][cc-by-nc-sa]

This work is licensed under a
[Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International License][cc-by-nc-sa].

[![CC BY-NC-SA 4.0][cc-by-nc-sa-image]][cc-by-nc-sa]

[cc-by-nc-sa]: http://creativecommons.org/licenses/by-nc-sa/4.0/
[cc-by-nc-sa-image]: https://licensebuttons.net/l/by-nc-sa/4.0/88x31.png
[cc-by-nc-sa-shield]: https://img.shields.io/badge/License-CC%20BY--NC--SA%204.0-lightgrey.svg

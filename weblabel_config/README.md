# Weblabel Visualization
OmegaPRIME files converted to OpenLABEL can be loaded into WebLabel, visualizing dynamic objects and OpenDRIVE files directly in WebLabel. An specific WebLabel version has been set-up as a service in the following [link](https://no-edit.d29gjk8l1b6x8x.amplifyapp.com/) for the Synergies project. To load your OpenLABEL files into the WebLABEL player service, you need to structure your input folder as follows:
```
├── misc/
│   └── empty_pcd.pcd
├── opendrive/
│    ├── your_map1.xodr
│    └── your_mapN.xodr
├── your_openlabel1.json
├── your_openlabelN.json 
└── structure.json
```
Where the opendrive and openlabel files correspond to the ones generated from the OmegaPRIME recordings. The OpenDRIVE files can be automatically written using the save_xodr function of the converter, specifying the desired folder where the map should be written.

Please contact mgarcia@vicomtech.org for the required username and password to use the online WebLABEL player service.

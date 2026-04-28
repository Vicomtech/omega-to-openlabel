import logging
import math
import uuid
import numpy as np
from dataclasses import dataclass
from typing import Dict, Tuple, Optional, Any
import os
import omega_prime
import vcd.core as core
import vcd.types as types
import vcd.utils as vcd_utils
from tqdm import tqdm

logger = logging.getLogger(__name__)

@dataclass
class ConverterConfig:
    """Configuration for the OmegaPRIME to OpenLABEL conversion."""
    openlabel_output_path: str
    scene_name: str
    save_pretty: bool = False
    apply_projections: bool = False


class Omega2Openlabel:
    """Transforms OmegaPRIME recordings into ASAM OpenLABEL format."""

    def __init__(self, recording: omega_prime.Recording, config: ConverterConfig):
        self.r = recording
        self.config = config
        if self.config.apply_projections:
            try:
                self.r.apply_projections()
            except Exception as e:
                print("Failed to apply projections: ", e)
        self.openlabel = core.OpenLABEL()

        # Initialize basic metadata
        self.openlabel.add_metadata_properties({"scene_name": self.config.scene_name})

    def convert(self, add_relations=False) -> None:
        """Executes the conversion pipeline."""
        logger.info(f"Starting conversion for scene: {self.config.scene_name}")

        self._add_coordinate_systems()
        self._add_xodr_stream()
        self._add_dynamic_objects()
        map_dict = self._add_static_objects()
        self._add_dynamic_data()
        if add_relations:
            self._add_located_relations(map_dict)

        self.openlabel.save(self.config.openlabel_output_path, pretty=self.config.save_pretty)
        logger.info(f"Successfully saved OpenLABEL file to {self.config.openlabel_output_path}")

    def _add_coordinate_systems(self) -> None:
        """Sets up the global and local coordinate systems."""
        self.openlabel.add_coordinate_system("odom", cs_type=types.CoordinateSystemType.scene_cs)

        c_matrix = np.array([0, 0, 0]).reshape(3, 1)
        r_matrix = vcd_utils.euler2R([0, 0, 0])
        scs_wrt_lcs = vcd_utils.create_pose(r_matrix, c_matrix)

        pose_data = types.PoseData(
            val=scs_wrt_lcs.flatten().tolist(),
            t_type=types.TransformDataType.matrix_4x4
        )
        self.openlabel.add_coordinate_system(
            name="vehicle-iso8855",
            cs_type=types.CoordinateSystemType.local_cs,
            parent_name="odom",
            pose_wrt_parent=pose_data
        )

    def _add_xodr_stream(self) -> None:
        """Adds the OpenDRIVE 3D empty stream for WebLABEL loading."""
        self.openlabel.add_stream(
            stream_name="OpenDRIVE",
            uri="misc/empty_pcd.pcd", # This is necessary as WebLABEL expects stream data which is not included in OmegaPRIME
            description="WebLABEL needs a 3D stream to load the map, loaded with an empty PCD file",
            stream_type=core.StreamType.lidar
        )
        self.openlabel.add_stream_properties("OpenDRIVE", properties={"coordinate_system": "odom"})

    def _add_static_objects(self) -> Dict[str, str]:
        """Adds OpenDRIVE map elements and establishes lane relationships.

        Returns:
            Dict[str, str]: A mapping of OmegaPRIME map IDs to OpenLABEL UIDs.
        """
        map_name = self.r.map.name
        self.openlabel.add_metadata_properties({"OpenDRIVE": map_name})
        self.openlabel.add_metadata_properties({"OpenDRIVE_path": f"/opendrive/{map_name}.xodr"})

        map_dict = {}

        for road in self.r.map.xodr_map.road_ids_to_object.values():
            road_name = f"{map_name}_ROAD{road.id}"
            self.openlabel.add_object(name=road_name, type="ROAD")

            for lane_section in road.lane_sections:
                section_name = f"{road_name}_SECTION{lane_section.lane_section_ordinal}"
                self.openlabel.add_object(name=section_name, type="SECTION")
                lane_dict = {}

                for lane in lane_section.lanes:
                    lane_type = "NONE" if lane.type is None else (
                        "LANE" if lane.type == "driving" else lane.type.upper())
                    lane_name = f"{section_name}_{lane_type}{lane.id}"

                    lane_uid = self.openlabel.add_object(name=lane_name, type=lane_type)
                    if lane_type == "LANE":
                        lane_dict[int(lane.id)] = lane_uid

                    map_dict[f"{road.id}{lane_section.lane_section_ordinal}{lane.id}"] = lane_uid

                self._process_lane_relations(lane_dict)

        return map_dict

    def _process_lane_relations(self, lane_dict: Dict[int, str]) -> None:
        """Helper to create 'isNextTo' relations for lanes."""
        for lane_id, lane_uid in lane_dict.items():
            id_next = 1 if lane_id == -1 else lane_id + 1
            id_prev = -1 if lane_id == 1 else lane_id - 1

            for adjacent_id in (id_next, id_prev):
                if adjacent_id in lane_dict:
                    relation_name = f"Relation{self.openlabel.get_num_relations()}"
                    self.openlabel.add_relation_object_object(
                        relation_name, 'isNextTo', lane_uid, lane_dict[adjacent_id]
                    )

    def _add_dynamic_objects(self) -> None:
        """Registers moving objects and extracts their semantic types and roles."""
        for obj_uid, obj in self.r.moving_objects.items():
            semantic_type = self._get_semantic_type(obj)
            uid = self.openlabel.add_object(
                name=str(uuid.uuid4()),
                semantic_type=semantic_type,
                uid=obj_uid
                )

            subtype_name = obj.subtype.name if obj.subtype is not None else "UNKNOWN"
            role_name = str(obj.role) if obj.role is not None else "UNKNOWN"
            self.openlabel.add_object_data(uid, types.text("subtype", str(subtype_name)))
            self.openlabel.add_object_data(uid, types.text("role", str(role_name)))


    def _add_dynamic_data(self) -> None:
        """Adds kinematics and bounding boxes for moving objects over time."""
        for uid, obj in tqdm(self.r.moving_objects.items(), desc="Processing Dynamic Data", leave=True):
            for i, nanos in enumerate(obj.nanos):
                # Safely handle missing frames
                frame_n = self.r.nanos2frame.get(math.trunc(nanos))
                if frame_n is None:
                    logger.debug(f"Frame not found for timestamp {nanos} on object {uid}. Skipping.")
                    continue

                acc_vec = [obj.acc_x[i], obj.acc_y[i], obj.acc_z[i]]
                vel_vec = [obj.vel_x[i], obj.vel_y[i], obj.vel_z[i]]
                cuboid = [
                    obj.x[i], obj.y[i], obj.z[i],
                    obj.roll[i], obj.pitch[i], obj.yaw[i],
                    obj.length, obj.width, obj.height
                ]

                self.openlabel.add_object_data(uid, types.vec("acceleration_vector", acc_vec), frame_value=frame_n)
                self.openlabel.add_object_data(uid, types.vec("velocity_vector", vel_vec), frame_value=frame_n)
                self.openlabel.add_object_data(uid, types.cuboid("bbox3D", cuboid, coordinate_system="odom"),
                                               frame_value=frame_n)

    def _add_located_relations(self, map_dict: Dict[str, str]) -> None:
        """Links moving objects to map elements (lanes/roads) over time intervals."""
        if not map_dict:
            logger.warning("Map dictionary is empty. Cannot process located relations.")
            return
        print("Loading omega locator, this may take a while for complex maps")
        locator = omega_prime.Locator.from_map(self.r.map)

        for obj_uid, mv in tqdm(self.r.moving_objects.items(), desc="Adding located relations", leave=True):
            relations = {}
            try:
                sts = locator.locate_mv(mv)
            except Exception as e:
                print(e)
                continue

            for i, loc in enumerate(sts.roadlane_id.data):
                frame_n = self.r.nanos2frame.get(math.trunc(mv.nanos[i]))
                if frame_n is None:
                    continue

                self.openlabel.add_object_data(obj_uid, types.num("longitudinalPos", sts.s.data[i]),
                                               frame_value=frame_n)
                self.openlabel.add_object_data(obj_uid, types.num("lateralPos", sts.t.data[i]), frame_value=frame_n)

                if loc is not None:
                    key = map_dict.get(f"{loc.road_id}{loc.section_id}{loc.lane_id}")
                    if not key:
                        continue

                    if key not in relations:
                        relations[key] = [(frame_n, frame_n)]
                    else:
                        # Time-series interval merging logic
                        if frame_n - relations[key][-1][1] == 1:
                            relations[key][-1] = (relations[key][-1][0], frame_n)
                        else:
                            relations[key].append((frame_n, frame_n))

            if not relations:
                logger.info(f"Object: {obj_uid} is not located in any map element")
            else:
                for key, value in relations.items():
                    relation_name = f"Relation{self.openlabel.get_num_relations()}"
                    self.openlabel.add_relation_object_object(
                        relation_name, 'isLocatedIn', obj_uid, key, frame_value=value
                    )

    def _get_semantic_type(self, obj: Any) -> str:
        """Extracts the base semantic type from an OmegaPRIME moving object."""
        try:
            semantic_type = obj.type.name
            if obj.subtype is not None:
                if "UNKNOWN" not in obj.subtype.name and "OTHER" not in obj.subtype.name:
                    semantic_type = obj.subtype.name

            # remove the "TYPE_" prefix
            return semantic_type.split("_")[-1]
        except Exception as e:
            print(f"Error extracting semantic type for object {obj.idx}: {e}, defaulting to UNKNOWN")
            return "UNKNOWN"

    def save_xodr(self, output_xodr_folder):
        xodr_path = os.path.join(output_xodr_folder, f"{self.r.map.name}.xodr")
        with open(xodr_path, "w") as f:
            f.write(self.r.map.odr_xml)
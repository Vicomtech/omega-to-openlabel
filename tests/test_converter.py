from omega_to_openlabel.converter import Omega2Openlabel, ConverterConfig
import omega_prime

INPUT_MCAP = "./tests/sample_data/bypassing_scenario1.mcap"

def test_without_relations(tmp_path):
    output_file = tmp_path / "test.json"
    omega_recording = omega_prime.Recording.from_file(INPUT_MCAP, parse_map=True)
    config = ConverterConfig(openlabel_output_path=str(output_file), scene_name="bypassing_test")
    o2l = Omega2Openlabel(omega_recording, config)
    o2l.convert()
    assert output_file.is_file()

def test_with_relations(tmp_path):
    output_file = tmp_path / "test_relations.json"
    omega_recording = omega_prime.Recording.from_file(INPUT_MCAP, parse_map=True)
    config = ConverterConfig(openlabel_output_path=str(output_file), scene_name="bypassing_test_relations")
    o2l = Omega2Openlabel(omega_recording, config)
    o2l.convert(add_relations=True)
    assert output_file.is_file()

def test_write_opendrive(tmp_path):
    omega_recording = omega_prime.Recording.from_file(INPUT_MCAP, parse_map=True)
    config = ConverterConfig(openlabel_output_path=str(tmp_path / "dummy.json"), scene_name="bypassing_test_relations")
    o2l = Omega2Openlabel(omega_recording, config)
    o2l.save_xodr(str(tmp_path))
    expected_file = tmp_path / "Town03.xodr"
    assert expected_file.is_file()



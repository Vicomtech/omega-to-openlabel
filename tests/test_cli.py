import pytest
import sys
import os
import tempfile
import json
from unittest import mock
from omega_to_openlabel.cli import main


@pytest.fixture
def sample_recording_path():
    return "./tests/sample_data/bypassing_scenario1.mcap"


@pytest.fixture
def temp_output_file():
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        temp_path = f.name
    yield temp_path
    if os.path.exists(temp_path):
        os.remove(temp_path)


@pytest.fixture
def temp_output_dir():
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup
    for file in os.listdir(temp_dir):
        os.remove(os.path.join(temp_dir, file))
    os.rmdir(temp_dir)


def test_successful_conversion_with_minimal_arguments(sample_recording_path, temp_output_file):
    sys.argv = ['omega-to-openlabel', '--input', sample_recording_path, '--output', temp_output_file]
    result = main()
    
    assert result == 0
    assert os.path.exists(temp_output_file)
    with open(temp_output_file, 'r') as f:
        data = json.load(f)
        assert 'openlabel' in data


def test_successful_conversion_with_all_optional_arguments(sample_recording_path, temp_output_file):
    sys.argv = [
        'omega-to-openlabel',
        '--input', sample_recording_path,
        '--output', temp_output_file,
        '--scene-name', 'test_scene',
        '--pretty',
        '--add-relations',
        '--verbose'
    ]
    result = main()
    
    assert result == 0
    assert os.path.exists(temp_output_file)
    with open(temp_output_file, 'r') as f:
        content = f.read()
        # Pretty flag should result in formatted JSON with indentation
        assert '\n' in content or '  ' in content


def test_missing_required_input_argument_raises_system_exit(temp_output_file):
    sys.argv = ['omega-to-openlabel', '--output', temp_output_file]
    with pytest.raises(SystemExit):
        main()


def test_missing_required_output_argument_raises_system_exit(sample_recording_path):
    sys.argv = ['omega-to-openlabel', '--input', sample_recording_path]
    with pytest.raises(SystemExit):
        main()


def test_nonexistent_input_file_returns_error(temp_output_file):
    sys.argv = [
        'omega-to-openlabel',
        '--input', './nonexistent_file.mcap',
        '--output', temp_output_file
    ]
    result = main()
    
    assert result == 1




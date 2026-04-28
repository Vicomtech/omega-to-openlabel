import argparse
import logging
import sys
from omega_to_openlabel.converter import Omega2Openlabel, ConverterConfig
import warnings
# these should be installed but we can check just in case
try:
    import omega_prime
except ImportError:
    omega_prime = None
    print("Warning: 'omega_prime' SDK is not installed. Please install it to use this converter.")

try:
    import vcd
except ImportError:
    vcd = None
    print("Warning: 'vcd' SDK is not installed. Please install it to use this converter.")


def main():
    parser = argparse.ArgumentParser(description="Convert OmegaPRIME recordings to ASAM OpenLABEL format.")
    
    parser.add_argument(
        "--input", "-i", 
        required=True, 
        help="Path to the OmegaPRIME recording (e.g., .mcap file or folder depending on SDK)."
    )
    parser.add_argument(
        "--output", "-o", 
        required=True, 
        help="Path for the output OpenLABEL JSON file."
    )
    parser.add_argument(
        "--scene-name", "-s", 
        default="omega_scene", 
        help="Name of the scene (default: omega_scene)."
    )
    parser.add_argument(
        "--pretty", 
        action="store_true", 
        help="Save the output JSON with indentation."
    )
    parser.add_argument(
        "--add-relations", 
        action="store_true", 
        help="Include lane relations and object-lane relations."
    )
    parser.add_argument(
        "--apply-projections",
        action="store_true",
        help="Apply OpenDRIVE map projection to the dynamic data."
    )
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose logging."
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    if not args.verbose:
        warnings.filterwarnings("ignore", module="omega_prime.*")

    logging.basicConfig(level=log_level, format="%(levelname)s: %(message)s")
    logger = logging.getLogger(__name__)

    if omega_prime is None:
        logger.error("The 'omega_prime' SDK is not installed. Please install it to use this converter.")
        return 1

    try:
        # Load the recording using omega_prime SDK
        # This part depends on how omega_prime expects to load recordings.
        # Often it's omega_prime.Recording(path) or similar.
        logger.info(f"Loading recording from {args.input}...")
        recording = omega_prime.Recording.from_file(args.input)

        config = ConverterConfig(
            openlabel_output_path=args.output,
            scene_name=args.scene_name,
            save_pretty=args.pretty,
            apply_projections=args.apply_projections
        )

        converter = Omega2Openlabel(recording, config)
        converter.convert(add_relations=args.add_relations)
        
        logger.info("Conversion completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"An error occurred during conversion: {e}")
        if args.verbose:
            logger.exception(e)
        return 1

if __name__ == "__main__":
    sys.exit(main())

"""Stage portable Data folders for a local build or a release archive."""

from pathlib import Path
import shutil
import sys


TEACHING_FILES = (
    "Neurons/TonicBursting_LightOffSustained.csv",
    "Neurons/TonicBursting_LightOffTransient.csv",
    "Neurons/TonicBursting_LightOnSustained.csv",
    "Neurons/TonicBursting_LightOnTransient.csv",
    "Neurons/TonicSpiking_LightOffSustained.csv",
    "Neurons/TonicSpiking_LightOffTransient.csv",
    "Neurons/TonicSpiking_LightOnSustained.csv",
    "Neurons/TonicSpiking_LightOnTransient.csv",
    "Stimuli/steps_10x15_10ms.csv",
    "Recordings/README.txt",
)


def stage_release_data(source, destination):
    """Copy the tracked teaching files and preserve existing destination files."""
    source = Path(source)
    destination = Path(destination) / "Data"
    for name in TEACHING_FILES:
        original = source / name
        target = destination / name
        if not original.is_file():
            raise FileNotFoundError(original)
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            output = target.open("xb")
        except FileExistsError:
            continue
        try:
            with output, original.open("rb") as input_file:
                shutil.copyfileobj(input_file, output)
        except OSError:
            target.unlink()
            raise


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("Usage: python stage_release_data.py DESTINATION")
    stage_release_data(Path(__file__).resolve().parents[1] / "Data", sys.argv[1])

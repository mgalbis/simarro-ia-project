import shutil
import zipfile
from pathlib import Path
from typing import Optional


BASE_DIR = Path(__file__).resolve().parents[2]
ARTIFACTS_DIR = BASE_DIR / "data" / "artifacts"


def save_uploaded_artifact(
    session_id: str,
    execution_id: str,
    filename: str,
    source_path: str,
) -> str:
    target_dir = ARTIFACTS_DIR / session_id / execution_id
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    target_path = target_dir / safe_name

    shutil.copyfile(source_path, target_path)

    return str(target_path)


def build_artifacts_zip(
    session_id: str,
    execution_id: str,
) -> Optional[Path]:
    artifact_dir = ARTIFACTS_DIR / session_id / execution_id

    if not artifact_dir.exists() or not artifact_dir.is_dir():
        return None

    zip_path = ARTIFACTS_DIR / session_id / f"{execution_id}_artifacts.zip"

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
      for file_path in artifact_dir.iterdir():
          if file_path.is_file():
              zip_file.write(file_path, arcname=file_path.name)

    return zip_path

def save_uploaded_artifact_bytes(
    session_id: str,
    execution_id: str,
    filename: str,
    content: bytes,
) -> str:
    target_dir = ARTIFACTS_DIR / session_id / execution_id
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = Path(filename).name
    target_path = target_dir / safe_name

    target_path.write_bytes(content)

    return str(target_path)
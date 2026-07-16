import os
import uuid

GENERATED_FOLDER = "generated"

os.makedirs(GENERATED_FOLDER, exist_ok=True)

def save_generated_rtl(code, extension=".v"):

    filename = f"{uuid.uuid4().hex}{extension}"

    filepath = os.path.join(
        GENERATED_FOLDER,
        filename
    )

    with open(filepath, "w") as f:
        f.write(code)

    return filepath
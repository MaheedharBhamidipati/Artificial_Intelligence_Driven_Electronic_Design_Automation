from fastapi import FastAPI
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os

from backend.schematic.schematic_generator import SchematicGenerator

app = FastAPI()


class SchematicRequest(BaseModel):
    filepath: str


@app.post("/generate_schematic")
def generate_schematic(req: SchematicRequest):

    output_svg = "backend/schematic/schematic.svg"

    generator = SchematicGenerator(req.filepath)
    generator.generate()

    return {
        "status": "success",
        "svg_path": output_svg
    }


@app.get("/schematic_svg")
def get_schematic_svg():
    return FileResponse("backend/schematic/schematic.svg")

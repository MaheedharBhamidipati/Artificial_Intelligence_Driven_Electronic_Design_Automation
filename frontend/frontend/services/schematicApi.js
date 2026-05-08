import axios from "axios";

const API = "http://localhost:8000";

export const generateSchematic = async (filepath) => {
  const res = await axios.post(`${API}/generate_schematic`, {
    filepath,
  });

  return res.data;
};

export const getSchematicSvgUrl = () => {
  return `${API}/schematic_svg`;
};
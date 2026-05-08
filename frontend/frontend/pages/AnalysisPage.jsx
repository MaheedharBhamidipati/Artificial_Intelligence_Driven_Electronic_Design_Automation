import React, { useState } from "react";
import CircuitViewer from "../components/CircuitViewer";
import {
  generateSchematic,
  getSchematicSvgUrl,
} from "../services/schematicApi";

const AnalysisPage = () => {
  const [svgUrl, setSvgUrl] = useState(null);

  const handleGenerate = async () => {
    await generateSchematic("backend/parser/example.v");

    setSvgUrl(
      `${getSchematicSvgUrl()}?t=${Date.now()}`
    );
  };

  return (
    <div className="p-6">
      <button
        onClick={handleGenerate}
        className="bg-blue-500 text-white px-4 py-2 rounded"
      >
        Generate Circuit Diagram
      </button>

      {svgUrl && (
        <div className="mt-6">
          <CircuitViewer svgUrl={svgUrl} />
        </div>
      )}
    </div>
  );
};

export default AnalysisPage;
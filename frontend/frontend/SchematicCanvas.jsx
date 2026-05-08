import React from "react";

const SchematicCanvas = ({ svgUrl }) => {
  return (
    <div className="w-full h-[800px] border rounded overflow-auto bg-white">
      <object
        data={svgUrl}
        type="image/svg+xml"
        className="w-full h-full"
      >
        Unable to load schematic.
      </object>
    </div>
  );
};

export default SchematicCanvas;
import React, { useState } from "react";

import SchematicCanvas from "./SchematicCanvas";
import SignalInspector from "./SignalInspector";

const CircuitViewer = ({ svgUrl }) => {
  const [selected, setSelected] = useState(null);

  return (
    <div className="grid grid-cols-4 gap-4">
      <div className="col-span-3">
        <SchematicCanvas svgUrl={svgUrl} />
      </div>

      <div className="col-span-1">
        <SignalInspector selected={selected} />
      </div>
    </div>
  );
};

export default CircuitViewer;
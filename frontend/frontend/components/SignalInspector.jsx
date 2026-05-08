import React from "react";

const SignalInspector = ({ selected }) => {
  if (!selected) {
    return (
      <div className="p-4 border rounded">
        Select a gate/signal to inspect
      </div>
    );
  }

  return (
    <div className="p-4 border rounded">
      <h3 className="font-bold mb-2">Inspector</h3>
      <pre>{JSON.stringify(selected, null, 2)}</pre>
    </div>
  );
};

export default SignalInspector;
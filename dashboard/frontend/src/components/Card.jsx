import React from "react";

const Card = ({ title, value, icon }) => (
  <div className="bg-cardBg rounded-xl shadow-card p-4 flex items-center gap-4">
    <div className="text-primary text-3xl">{icon}</div>
    <div>
      <p className="text-textLight text-sm">{title}</p>
      <p className="text-textDark text-xl font-semibold">{value}</p>
    </div>
  </div>
);

export default Card;

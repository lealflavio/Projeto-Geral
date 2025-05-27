import React from "react";

const Card = ({ title, value, icon }) => (
  <div className="bg-card hover:bg-card-hover rounded-lg shadow-card hover:shadow-card-hover transition-all duration-normal p-md flex items-center gap-md">
    <div className="text-primary-500 text-3xl">{icon}</div>
    <div>
      <p className="text-muted text-sm">{title}</p>
      <p className="text-text-dark text-xl font-semibold">{value}</p>
    </div>
  </div>
);

export default Card;

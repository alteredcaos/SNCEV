import React, { createContext, useContext, useState } from "react";

const RoleContext = createContext({ role: "vacunador", setRole: () => {} });

export function RoleProvider({ children }) {
  const [role, setRole] = useState("vacunador");
  return (
    <RoleContext.Provider value={{ role, setRole }}>
      {children}
    </RoleContext.Provider>
  );
}

export const useRole = () => useContext(RoleContext);
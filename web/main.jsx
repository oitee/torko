import React from "react";
import { createRoot } from "react-dom/client";
import { RouterProvider } from "react-router-dom";
// The base styles load first, so that the styles of each component and page come later and win.
import "./assets/css/tokens.css";
import "./assets/css/base.css";
import { router } from "./router.jsx";

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <RouterProvider router={router} />
  </React.StrictMode>
);

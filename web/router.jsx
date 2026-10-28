import { createBrowserRouter } from "react-router-dom";
import Layout from "./components/Layout.jsx";
import Home from "./pages/home.jsx";
import Tag from "./pages/tag.jsx";
import Member from "./pages/member.jsx";
import Speech from "./pages/speech.jsx";
import Debate from "./pages/debate.jsx";
import Place from "./pages/place.jsx";
import Search from "./pages/search.jsx";
import NotFound from "./pages/not_found.jsx";
import DevComponents from "./pages/dev_components.jsx";

// Each address of the site and the page that it shows. Flask sends index.html for every one of them.
export const routes = [
  {
    element: <Layout />,
    children: [
      { path: "/", element: <Home /> },
      { path: "/tag/:slug", element: <Tag /> },
      { path: "/member/:id", element: <Member /> },
      { path: "/speech/:id", element: <Speech /> },
      { path: "/debate/:id", element: <Debate /> },
      { path: "/place/:slug", element: <Place /> },
      { path: "/search", element: <Search /> },
      // The components page exists only in development. The live site has no such address.
      ...(import.meta.env.DEV ? [{ path: "/dev/components", element: <DevComponents /> }] : []),
      { path: "*", element: <NotFound /> },
    ],
  },
];

export const router = createBrowserRouter(routes);

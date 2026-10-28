# web: the public site

This folder holds the new public site of Torko. The old dashboard in `static/` will be deprecated.

## Tools

- **React** is a JavaScript library. It builds a page from small reusable parts, called components. For example, one component draws a speech row, and every list of speeches uses that component.
- **Vite** is a build tool. During development it serves the pages and reloads them when a file changes. For the live site it converts the source files into plain HTML, CSS, and JavaScript files in `web/dist/`.
- **Flask** is the Python web server of Torko (`server.py`). It serves the built files from `web/dist/` and the data under `/api/`.
- **Single-page app.** The site has one HTML file. When the reader opens another page, JavaScript in the browser changes the content. The browser does not load a new HTML file.
- **Fonts** load from Google Fonts.

## Folders

| Path | Holds |
|---|---|
| `index.html` | The one HTML file of the site. Flask sends it for every page address. |
| `router.jsx` | Maps each address, for example `/member/123`, to one page component. |
| `components/Layout.jsx` | The header, footer and theme, shared by all pages. |
| `pages/` | One component for each page: home, tag, member, speech, debate, place, search. A `.jsx` file is JavaScript with HTML-like markup for React. |
| `assets/css/tokens.css` | The colours, fonts, and spacing of the design, as CSS variables, for the light and the dark theme. |
| `assets/js/api.js` | One helper that calls `/api/...` and handles errors. |
| `assets/js/format.js` | Shared text: dates, numbers, "Speaker not identified". |
| `assets/vendor/` | Files from third parties. |

`web/node_modules/` (installed packages) and `web/dist/` (build output) are not in git.

## Status

The folders exist. The build setup, the shared components, and the pages are not written yet.

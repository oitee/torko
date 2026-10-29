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
| `components/` | The shared parts of the pages, for example `SpeechRow`, `Chart`, `FilterBar`, and `SearchBox`. `Layout.jsx` holds the header, the footer, and the theme. Each component has its own CSS file. |
| `pages/` | One component for each page: home, tag, member, speech, debate, place, search. A sub-folder, for example `pages/tag/`, holds the parts of one page. A `.jsx` file is JavaScript with HTML-like markup for React. |
| `assets/css/tokens.css` | The colours, fonts, and spacing of the design, as CSS variables, for the light and the dark theme. |
| `assets/js/api.js` | One helper that calls `/api/...` and handles errors. |
| `assets/js/format.js` | Shared text: dates, numbers, "Speaker not identified". |
| `assets/js/colour.js` | The colour of each party. |
| `assets/js/site.js` | The public address of the site and the contact email, from `VITE_SITE_URL` and `VITE_CONTACT_EMAIL` in the `.env` file of the repository root. |
| `tests/` | The tests, one file for each component and each page. They run with Vitest and Testing Library. |
| `assets/vendor/` | Files from third parties. |

`web/node_modules/` (installed packages) and `web/dist/` (build output) are not in git.

## Run it

You need Node.js 22. Install the packages once:

```bash
cd web && npm install
```

During development, run Flask and Vite at the same time. Flask sends the data on port 5050. Vite shows the site on port 5173 and sends each `/api/` call on to Flask.

```bash
python3 server.py
```

```bash
cd web && npm run dev
```

Open http://localhost:5173.

Run the tests:

```bash
cd web && npm test
```

Build the site into `web/dist/`:

```bash
cd web && npm run build
```

## Status

Six pages work: Tag, Member, Speech, Debate, Place, and Search. Each page reads its data from `/api/`. The Home page is not built yet. It shows only a placeholder.

Flask sends the built site for the addresses `/tag/...`, `/member/...`, `/speech/...`, `/debate/...`, `/place/...`, and `/search`. The address `/` still opens the older dashboard in `static/`. That changes when the Home page is built.

The address `/dev/components` shows every shared component. It exists only during development.

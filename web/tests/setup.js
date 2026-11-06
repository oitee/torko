// jsdom has no window.scrollTo. The router calls it on each new page.
window.scrollTo = () => {};

import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <main className="page">
      <h1>Page not found</h1>
      <p>
        Torko has no page at this address. <Link to="/">Go to the home page</Link>.
      </p>
    </main>
  );
}

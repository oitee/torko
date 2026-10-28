import { useParams } from "react-router-dom";

// Search page. Not built yet. Mockup: design/mockups/v14/Torko Search.dc.html.
export default function Search() {
  const params = useParams();
  return (
    <main className="page">
      <h1>Search</h1>
      <p className="meta">{JSON.stringify(params)}</p>
    </main>
  );
}

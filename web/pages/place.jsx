import { useParams } from "react-router-dom";

// Place page. Not built yet. Mockup: design/mockups/v14/Torko Place.dc.html.
export default function Place() {
  const params = useParams();
  return (
    <main className="page">
      <h1>Place</h1>
      <p className="meta">{JSON.stringify(params)}</p>
    </main>
  );
}

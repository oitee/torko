import { useParams } from "react-router-dom";

// Tag page. Not built yet. Mockup: design/mockups/v14/Torko Tag.dc.html.
export default function Tag() {
  const params = useParams();
  return (
    <main className="page">
      <h1>Tag</h1>
      <p className="meta">{JSON.stringify(params)}</p>
    </main>
  );
}

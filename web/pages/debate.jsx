import { useParams } from "react-router-dom";

// Debate page. Not built yet. Mockup: design/mockups/v14/Torko Debate v3.dc.html.
export default function Debate() {
  const params = useParams();
  return (
    <main className="page">
      <h1>Debate</h1>
      <p className="meta">{JSON.stringify(params)}</p>
    </main>
  );
}

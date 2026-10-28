import { useParams } from "react-router-dom";

// Speech page. Not built yet. Mockup: design/mockups/v14/Torko Speech.dc.html.
export default function Speech() {
  const params = useParams();
  return (
    <main className="page">
      <h1>Speech</h1>
      <p className="meta">{JSON.stringify(params)}</p>
    </main>
  );
}

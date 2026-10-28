import { useParams } from "react-router-dom";

// Member page. Not built yet. Mockup: design/mockups/v14/Torko Member v2.dc.html.
export default function Member() {
  const params = useParams();
  return (
    <main className="page">
      <h1>Member</h1>
      <p className="meta">{JSON.stringify(params)}</p>
    </main>
  );
}

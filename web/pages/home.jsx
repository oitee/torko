import { useParams } from "react-router-dom";

// Home page. Not built yet. Mockup: design/mockups/v14/Torko Home v2.dc.html.
export default function Home() {
  const params = useParams();
  return (
    <main className="page">
      <h1>Home</h1>
      <p className="meta">{JSON.stringify(params)}</p>
    </main>
  );
}

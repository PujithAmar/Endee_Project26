import "@/App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { Toaster } from "sonner";
import Analyzer from "@/pages/Analyzer";
import History from "@/pages/History";
import Chat from "@/pages/Chat";
import Navbar from "@/components/Navbar";

function App() {
  return (
    <div className="App grain">
      <div className="bg-aurora" />
      <BrowserRouter>
        <Navbar />
        <Routes>
          <Route path="/" element={<Analyzer />} />
          <Route path="/history" element={<History />} />
          <Route path="/history/:id" element={<Analyzer />} />
          <Route path="/chat/:sessionId" element={<Chat />} />
        </Routes>
        <Toaster
          theme="dark"
          toastOptions={{
            style: {
              background: "#181D27",
              border: "1px solid #222834",
              color: "#EDEFF3",
            },
          }}
        />
      </BrowserRouter>
    </div>
  );
}

export default App;

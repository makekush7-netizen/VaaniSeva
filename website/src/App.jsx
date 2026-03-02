import React from 'react'
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Navbar from './components/layout/Navbar'
import Home from './pages/Home'
import TryPage from './pages/TryPage'
import VaaniWidget from './components/VaaniAgent/VaaniWidget'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

function App() {
  return (
    <Router>
      <div className="min-h-screen bg-white text-content-primary font-sans">
        <Navbar />
        <main>
          <Routes>
            <Route path="/" element={<Home />} />
            <Route path="/try" element={<TryPage />} />
          </Routes>
        </main>

        {/* Floating AI Agent — visible on every page */}
        <VaaniWidget apiBaseUrl={API_BASE} />
      </div>
    </Router>
  )
}

export default App

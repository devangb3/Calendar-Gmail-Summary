import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';

// Configure axios to send credentials (cookies) with requests
axios.defaults.withCredentials = true;

function SummaryPage() {
  const [summaryData, setSummaryData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        setLoading(true);
        console.log("Fetching summary...");
        const response = await axios.get('http://localhost:5000/api/summary'); // Ensure this matches your backend URL
        setSummaryData(response.data);
        setError(null);
      } catch (err) {
        console.error("Error fetching summary:", err);
        if (err.response && err.response.status === 401) {
          // If unauthorized, redirect to login
          navigate('/login');
        } else {
          setError(err.response?.data?.error || err.message || 'Failed to fetch summary');
        }
        setSummaryData(null);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, [navigate]);

  const handleLogout = async () => {
    try {
      await axios.post('http://localhost:5000/api/logout'); // Ensure this matches your backend URL
      navigate('/login');
    } catch (err) {
      console.error("Error logging out:", err);
      setError(err.response?.data?.error || err.message || 'Failed to log out');
    }
  };

  return (
    <div>
      <h2>Your Summary</h2>
      {loading && <p>Loading summary...</p>}
      {error && <p style={{ color: 'red' }}>Error: {error}</p>}
      {summaryData && (
        <div>
          <h3>Generated Summary:</h3>
          {/* Render summary text preserving line breaks */}
          <pre style={{ whiteSpace: 'pre-wrap', wordWrap: 'break-word', fontFamily: 'inherit' }}>
            {summaryData.summary}
          </pre>
          <hr />
          <p>
            <a href={summaryData.calendarLink} target="_blank" rel="noopener noreferrer">Open Google Calendar</a>
          </p>
          <p>
            <a href={summaryData.gmailLink} target="_blank" rel="noopener noreferrer">Open Gmail</a>
          </p>
        </div>
      )}
      <button onClick={handleLogout} style={{ marginTop: '20px' }}>Logout</button>
    </div>
  );
}

export default SummaryPage;

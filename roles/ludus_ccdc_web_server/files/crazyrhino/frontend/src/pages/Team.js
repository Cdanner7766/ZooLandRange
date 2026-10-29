import React, { useEffect, useState } from 'react';
import api from '../api';
import './Team.css';

export default function Team() {
  const [team, setTeam] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get('/team').then(res => setTeam(res.data)).catch(() => {}).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="loading">Loading team...</div>;

  return (
    <div className="team-page">
      <div className="page-header">
        <h1>Meet the Team</h1>
        <p>The staff who keep Wild Kingdom Zoo running, from the gift shop to the savanna.</p>
      </div>

      <div className="container team-grid">
        {team.map(person => (
          <div key={person.email} className="card team-card">
            <div className="team-avatar">🙂</div>
            <h3>{person.name}</h3>
            <p className="team-dept">{person.department}</p>
            <a className="team-email" href={`mailto:${person.email}`}>{person.email}</a>
          </div>
        ))}
      </div>
    </div>
  );
}

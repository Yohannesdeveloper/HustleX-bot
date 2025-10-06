// webapp/src/ProfileWizard.jsx (simplified)
import React, {useState, useEffect} from 'react';

export default function ProfileWizard(){
  const [name, setName] = useState('');
  const [age, setAge] = useState('');
  const [sex, setSex] = useState('');
  const [cvFile, setCvFile] = useState(null);

  useEffect(() => {
    if (window.Telegram?.WebApp) window.Telegram.WebApp.expand();
  }, []);

  async function submit(e){
    e.preventDefault();
    const initData = window.Telegram?.WebApp?.initData || '';
    const fd = new FormData();
    fd.append('name', name);
    fd.append('age', age);
    fd.append('sex', sex);
    fd.append('initData', initData);
    if (cvFile) fd.append('cv', cvFile);

    const res = await fetch('/api/profile', { method: 'POST', body: fd });
    if (res.ok) window.Telegram.WebApp.close();
    else alert('Save failed');
  }

  return (
    <form onSubmit={submit} style={{padding:20}}>
      <h2 style={{color:'#00bcd4'}}>HustleX — Create Profile</h2>
      <label>Name</label><input value={name} onChange={e=>setName(e.target.value)} />
      <label>Age</label><input type="number" value={age} onChange={e=>setAge(e.target.value)} />
      <label>Sex</label>
      <select value={sex} onChange={e=>setSex(e.target.value)}>
        <option value="">Select</option><option value="male">Male</option><option value="female">Female</option><option value="other">Other</option>
      </select>
      <label>Upload CV (PDF)</label>
      <input type="file" accept=".pdf" onChange={e=>setCvFile(e.target.files[0])} />
      <button type="submit">Save profile</button>
    </form>
  );
}

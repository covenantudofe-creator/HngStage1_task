import React, { useEffect, useMemo, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { CalendarDays, Check, ChevronLeft, ChevronRight, Clock3, Edit3, Film, Plus, Trash2, X } from 'lucide-react';
import './styles.css';

const API = 'http://127.0.0.1:8000/api';
const pad = (n) => String(n).padStart(2, '0');
const toISO = (d) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
const today = new Date();

function App() {
  const [tasks, setTasks] = useState([]);
  const [selectedDate, setSelectedDate] = useState(toISO(today));
  const [month, setMonth] = useState(new Date(today.getFullYear(), today.getMonth(), 1));
  const [statusFilter, setStatusFilter] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [toast, setToast] = useState('');

  const loadTasks = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/tasks`);
      if (!res.ok) throw new Error('Could not load tasks');
      setTasks(await res.json());
    } catch {
      setToast('Start the FastAPI server to load your tasks.');
    } finally { setLoading(false); }
  };

  useEffect(() => { loadTasks(); }, []);
  useEffect(() => { if (toast) { const t = setTimeout(() => setToast(''), 3000); return () => clearTimeout(t); } }, [toast]);

  const selectedTasks = useMemo(() => tasks.filter(t => t.task_date === selectedDate && (statusFilter === 'all' || t.status === statusFilter)), [tasks, selectedDate, statusFilter]);
  const stats = useMemo(() => ({ total: tasks.length, done: tasks.filter(t => t.status === 'completed').length, active: tasks.filter(t => t.status === 'in_progress').length }), [tasks]);

  const days = useMemo(() => {
    const first = new Date(month.getFullYear(), month.getMonth(), 1);
    const start = new Date(first); start.setDate(first.getDate() - first.getDay());
    return Array.from({ length: 42 }, (_, i) => { const d = new Date(start); d.setDate(start.getDate() + i); return d; });
  }, [month]);

  const submitTask = async (data) => {
    const method = editing ? 'PUT' : 'POST';
    const url = editing ? `${API}/tasks/${editing.id}` : `${API}/tasks`;
    try {
      const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(data) });
      if (!res.ok) throw new Error('Save failed');
      await loadTasks(); setShowForm(false); setEditing(null); setToast(editing ? 'Task updated.' : 'Task added to your schedule.');
    } catch { setToast('Could not save the task. Is the backend running?'); }
  };

  const toggleTask = async (id) => {
    try { await fetch(`${API}/tasks/${id}/status`, { method: 'PATCH' }); await loadTasks(); }
    catch { setToast('Could not update task status.'); }
  };

  const removeTask = async (id) => {
    if (!confirm('Delete this task?')) return;
    try { await fetch(`${API}/tasks/${id}`, { method: 'DELETE' }); await loadTasks(); setToast('Task deleted.'); }
    catch { setToast('Could not delete the task.'); }
  };

  const changeDay = (d) => { const iso = toISO(d); setSelectedDate(iso); if (d.getMonth() !== month.getMonth()) setMonth(new Date(d.getFullYear(), d.getMonth(), 1)); };
  const monthLabel = month.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  const selectedLabel = new Date(`${selectedDate}T12:00:00`).toLocaleDateString('en-US', { weekday: 'long', month: 'long', day: 'numeric' });

  return <div className="app">
    <header className="hero">
      <div className="nav"><div className="brand"><span className="brand-mark"><Film size={19}/></span><span>HNG<span>STAGE 1</span></span></div><div className="nav-pill"><span className="live-dot"/> DAILY PLANNER</div></div>
      <div className="hero-content"><div><p className="eyebrow">YOUR NEXT SCENE</p><h1>Make today <em>count.</em></h1><p className="hero-copy">Organize your day like a story worth finishing. One scene, one task, one win at a time.</p></div><button className="primary" onClick={() => {setEditing(null); setShowForm(true)}}><Plus size={18}/> Add Task</button></div>
      <div className="hero-fade"/>
    </header>

    <main className="shell">
      <section className="stats"><Stat label="ALL TASKS" value={stats.total}/><Stat label="IN PROGRESS" value={stats.active}/><Stat label="COMPLETED" value={stats.done}/><div className="progress-wrap"><div className="progress-top"><span>DAY PROGRESS</span><b>{stats.total ? Math.round(stats.done / stats.total * 100) : 0}%</b></div><div className="progress"><span style={{width: `${stats.total ? stats.done / stats.total * 100 : 0}%`}}/></div></div></section>

      <section className="workspace">
        <aside className="calendar-panel">
          <div className="panel-heading"><div><p className="kicker">SCHEDULE</p><h2>Calendar</h2></div><CalendarDays size={22}/></div>
          <div className="calendar-nav"><button onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() - 1, 1))}><ChevronLeft/></button><strong>{monthLabel}</strong><button onClick={() => setMonth(new Date(month.getFullYear(), month.getMonth() + 1, 1))}><ChevronRight/></button></div>
          <div className="weekdays">{['SUN','MON','TUE','WED','THU','FRI','SAT'].map(x => <span key={x}>{x}</span>)}</div>
          <div className="days">{days.map((d, i) => { const iso=toISO(d); const count=tasks.filter(t=>t.task_date===iso).length; return <button key={i} className={`day ${d.getMonth() !== month.getMonth() ? 'muted':''} ${iso===selectedDate?'selected':''} ${iso===toISO(today)?'today':''}`} onClick={()=>changeDay(d)}><span>{d.getDate()}</span>{count>0 && <i>{count}</i>}</button> })}</div>
          <button className="today-btn" onClick={()=>{setSelectedDate(toISO(today));setMonth(new Date(today.getFullYear(),today.getMonth(),1))}}>Jump to today</button>
        </aside>

        <section className="tasks-panel">
          <div className="tasks-header"><div><p className="kicker">YOUR TIMELINE</p><h2>{selectedLabel}</h2></div><div className="filters">{[['all','All'],['in_progress','In Progress'],['completed','Completed']].map(([v,l])=><button key={v} className={statusFilter===v?'active':''} onClick={()=>setStatusFilter(v)}>{l}</button>)}</div></div>
          {loading ? <div className="empty"><div className="loader"/><p>Loading your story...</p></div> : selectedTasks.length === 0 ? <div className="empty"><div className="empty-icon"><Film/></div><h3>No scenes scheduled.</h3><p>Nothing is playing for this day yet. Add your next task.</p><button className="outline" onClick={()=>{setEditing(null);setShowForm(true)}}><Plus size={16}/> Create a task</button></div> : <div className="task-list">{selectedTasks.map(task => <article className={`task-card ${task.status==='completed'?'done':''}`} key={task.id}><div className="time"><Clock3 size={15}/><span>{formatTime(task.task_time)}</span></div><button className={`check ${task.status==='completed'?'checked':''}`} onClick={()=>toggleTask(task.id)} aria-label="Toggle task status">{task.status==='completed' && <Check size={16}/>}</button><div className="task-main"><div className="task-top"><h3>{task.title}</h3><span className={`badge ${task.status}`}>{task.status==='completed'?'COMPLETED':'IN PROGRESS'}</span></div><p>{task.description || 'No description added.'}</p><div className="task-meta"><span>{task.section}</span><span>•</span><span>{task.task_date}</span></div></div><div className="actions"><button onClick={()=>{setEditing(task);setShowForm(true)}}><Edit3 size={16}/></button><button onClick={()=>removeTask(task.id)}><Trash2 size={16}/></button></div></article>)}</div>}
        </section>
      </section>
    </main>

    <footer>© 2026 HNG <span>STAGE 1</span> <small>— Task Manager.</small></footer>
    {showForm && <TaskModal task={editing} defaultDate={selectedDate} onClose={()=>{setShowForm(false);setEditing(null)}} onSubmit={submitTask}/>} 
    {toast && <div className="toast">{toast}</div>}
  </div>
}

function Stat({label,value}) { return <div className="stat"><span>{label}</span><strong>{value}</strong></div> }
function formatTime(t) { const [h,m]=t.split(':').map(Number); const d=new Date(); d.setHours(h,m); return d.toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'}); }

function TaskModal({task, defaultDate, onClose, onSubmit}) {
  const [form,setForm]=useState(task ? {...task} : {title:'',section:'Personal',description:'',task_date:defaultDate,task_time:'09:00',status:'in_progress'});
  const set=(k,v)=>setForm(x=>({...x,[k]:v}));
  return <div className="modal-backdrop"><div className="modal"><div className="modal-head"><div><p className="kicker">{task?'EDIT SCENE':'NEW SCENE'}</p><h2>{task?'Update task':'Add a task'}</h2></div><button onClick={onClose}><X/></button></div><form onSubmit={e=>{e.preventDefault();onSubmit(form)}}><label>Task title<input required value={form.title} onChange={e=>set('title',e.target.value)} placeholder="e.g. Finish React project"/></label><div className="two"><label>Section<select value={form.section} onChange={e=>set('section',e.target.value)}><option>Personal</option><option>Work</option><option>Study</option><option>Health</option><option>Projects</option></select></label><label>Status<select value={form.status} onChange={e=>set('status',e.target.value)}><option value="in_progress">In Progress</option><option value="completed">Completed</option></select></label></div><div className="two"><label>Date<input type="date" required value={form.task_date} onChange={e=>set('task_date',e.target.value)}/></label><label>Time<input type="time" required value={form.task_time} onChange={e=>set('task_time',e.target.value)}/></label></div><label>Description<textarea value={form.description} onChange={e=>set('description',e.target.value)} placeholder="What needs to happen in this scene?" rows="4"/></label><button className="primary full" type="submit">{task?'Save changes':'Add to timeline'}</button></form></div></div>
}

createRoot(document.getElementById('root')).render(<App/>);

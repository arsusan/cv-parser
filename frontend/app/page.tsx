
'use client';
/* eslint-disable @typescript-eslint/no-explicit-any */
import { useEffect, useRef, useState } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

const badge: Record<string, string> = {
  valid: 'bg-green-100 text-green-800',
  warnings: 'bg-yellow-100 text-yellow-800',
  invalid: 'bg-red-100 text-red-800',
  failed: 'bg-red-100 text-red-800',
};

function Row({ k, v }: { k: string; v: any }) {
  const text = Array.isArray(v) ? (v.length ? v.join(', ') : '-') : (v ?? '-');
  return (
    <div>
      <dt className="text-gray-500">{k}</dt>
      <dd>{String(text)}</dd>
    </div>
  );
}

export default function Home() {
  const [models, setModels] = useState<any[]>([]);
  const [model, setModel] = useState('');
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [version, setVersion] = useState(0);
  const [out, setOut] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (selectedFile: File | undefined) => {
    if (!selectedFile) return;

    const validExtension = /\.(pdf|docx)$/i.test(selectedFile.name);

    if (!validExtension) {
      setErr('Please select a PDF or DOCX file.');
      return;
    }

    setFile(selectedFile);
    setErr('');
  };

  const removeFile = () => {
    setFile(null);
    setErr('');
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const loadPrompt = async () => {
    const j = await (await fetch(`${API}/prompt`)).json();
    setPrompt(j.text);
    setVersion(j.version);
  };

  const loadStats = async () =>
    setStats(await (await fetch(`${API}/stats`)).json());

  useEffect(() => {
    fetch(`${API}/models`)
      .then((r) => r.json())
      .then((m) => {
        setModels(m);
        setModel(m[0]?.id || '');
      })
      .catch(() => setErr('Cannot reach the API. Is the backend running?'));

    loadPrompt();
    loadStats();
  }, []);

  const savePrompt = async (reset: boolean) => {
    const r = await fetch(reset ? `${API}/prompt/reset` : `${API}/prompt`, {
      method: reset ? 'POST' : 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: reset ? undefined : JSON.stringify({ text: prompt }),
    });

    const j = await r.json();
    setPrompt(j.text);
    setVersion(j.version);
  };

  const parse = async () => {
    if (!file) return;

    setLoading(true);
    setErr('');
    setOut(null);

    const fd = new FormData();
    fd.append('file', file);
    fd.append('model', model);

    try {
      const r = await fetch(`${API}/parse`, {
        method: 'POST',
        body: fd,
      });

      const j = await r.json();

      if (!r.ok) throw new Error(j.detail || 'Request failed');

      setOut(j);
      loadStats();
    } catch (e: any) {
      setErr(e.message);
    } finally {
      setLoading(false);
    }
  };

  const r = out?.result;
  const v = out?.validation;

  return (
    <main className="mx-auto max-w-6xl space-y-6 p-6 text-gray-900">
      <h1 className="text-2xl font-bold">AI CV Parser</h1>

      <div className="grid gap-6 md:grid-cols-2">

        {/* Upload and model section */}
        <section className="space-y-4 rounded-xl border border-gray-200 bg-white p-5 shadow-sm">
          <h2 className="font-semibold text-gray-800">
            1. Upload and model
          </h2>

          {/* File upload area */}
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragActive(true);
            }}
            onDragLeave={(e) => {
              e.preventDefault();
              setDragActive(false);
            }}
            onDrop={(e) => {
              e.preventDefault();
              setDragActive(false);
              handleFile(e.dataTransfer.files?.[0]);
            }}
            className={`rounded-xl border-2 border-dashed p-6 text-center transition-all ${
              dragActive
                ? 'border-indigo-500 bg-indigo-100'
                : 'border-indigo-200 bg-indigo-50/50 hover:border-indigo-400 hover:bg-indigo-50'
            }`}
          >
            <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-full bg-indigo-100">
              <svg
                className="h-7 w-7 text-indigo-600"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="1.8"
                  d="M12 16V4m0 0L7 9m5-5l5 5M4 16v3a1 1 0 001 1h14a1 1 0 001-1v-3"
                />
              </svg>
            </div>

            <h3 className="text-sm font-semibold text-gray-800">
              {dragActive
                ? 'Drop your CV here'
                : file
                  ? 'CV selected successfully'
                  : 'Upload your CV'}
            </h3>

            <p className="mt-1 text-xs text-gray-500">
              {file
                ? 'Your document is ready for parsing'
                : 'Drag and drop your file here or browse your computer'}
            </p>

            <label className="mt-4 inline-flex cursor-pointer items-center gap-2 rounded-lg bg-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm transition hover:bg-indigo-700 hover:shadow-md">
              <svg
                className="h-4 w-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth="2"
                  d="M12 4v16m8-8H4"
                />
              </svg>

              {file ? 'Choose Another File' : 'Choose File'}

              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.docx"
                className="hidden"
                onChange={(e) => handleFile(e.target.files?.[0])}
              />
            </label>

            <div className="mt-4 flex justify-center gap-2">
              <span className="rounded-md border border-red-200 bg-white px-2 py-1 text-xs font-medium text-red-600">
                PDF
              </span>
              <span className="rounded-md border border-blue-200 bg-white px-2 py-1 text-xs font-medium text-blue-600">
                DOCX
              </span>
              <span className="self-center text-xs text-gray-400">
                Supported formats
              </span>
            </div>
          </div>

          {/* Selected file information */}
          {file && (
            <div className="flex items-center justify-between rounded-lg border border-gray-200 bg-white p-3 shadow-sm">
              <div className="flex min-w-0 items-center gap-3">
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-indigo-100">
                  <svg
                    className="h-5 w-5 text-indigo-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth="1.8"
                      d="M7 3h7l5 5v13H7a2 2 0 01-2-2V5a2 2 0 012-2z"
                    />
                    <path
                      stroke="currentColor"
                      strokeWidth="1.5"
                      d="M14 3v5h5M9 13h6m-6 4h6"
                    />
                  </svg>
                </div>

                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-gray-800">
                    {file.name}
                  </p>
                  <p className="text-xs text-gray-500">
                    {(file.size / 1024).toFixed(1)} KB · Ready to upload
                  </p>
                </div>
              </div>

              <button
                type="button"
                onClick={removeFile}
                className="ml-2 shrink-0 rounded-md px-2 py-1 text-xs font-medium text-red-500 hover:bg-red-50"
              >
                Remove
              </button>
            </div>
          )}

          {/* Model selection */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-gray-700">
              AI Model
            </label>

            <select
              className="w-full rounded-lg border border-gray-300 bg-white p-2.5 text-sm outline-none transition focus:border-indigo-500 focus:ring-2 focus:ring-indigo-100"
              value={model}
              onChange={(e) => setModel(e.target.value)}
            >
              {models.map((m) => (
                <option key={m.id} value={m.id}>
                  {m.free ? '[free] ' : ''}
                  {m.id}
                </option>
              ))}
            </select>
          </div>

          {/* Parse button */}
          <button
            className="w-full rounded-lg bg-indigo-600 px-4 py-3 font-semibold text-white shadow-sm transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={!file || loading}
            onClick={parse}
          >
            {loading ? 'Parsing CV...' : 'Parse CV'}
          </button>

          {err && (
            <p className="rounded-lg bg-red-50 p-3 text-sm text-red-600">
              {err}
            </p>
          )}
        </section>

        {/* Prompt section - unchanged */}
        <section className="space-y-3 rounded border p-4">
          <h2 className="font-semibold">
            2. Prompt (active version {version})
          </h2>

          <textarea
            className="h-56 w-full rounded border p-2 font-mono text-xs"
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
          />

          <div className="flex gap-2">
            <button
              className="rounded bg-green-600 px-3 py-1 text-white"
              onClick={() => savePrompt(false)}
            >
              Save prompt
            </button>

            <button
              className="rounded bg-gray-600 px-3 py-1 text-white"
              onClick={() => savePrompt(true)}
            >
              Reset to default
            </button>
          </div>
        </section>
      </div>

      {/* Results section - unchanged */}
      {out && (
        <>
          <div className="grid gap-6 md:grid-cols-2">
            <section className="rounded border p-4">
              <h2 className="mb-2 font-semibold">3. Validation</h2>

              <span className={`rounded px-2 py-1 text-sm ${badge[v?.status] || ''}`}>
                {v?.status}
              </span>

              <ul className="mt-3 text-sm">
                {Object.entries(v?.checks || {}).map(([k, ok]) => (
                  <li key={k}>
                    {ok ? 'PASS' : 'FAIL'} - {k}
                  </li>
                ))}
              </ul>

              {(v?.errors || []).map((e: string, i: number) => (
                <p key={i} className="mt-1 text-sm text-red-700">
                  {e}
                </p>
              ))}

              {(v?.warnings || []).map((e: string, i: number) => (
                <p key={i} className="mt-1 text-sm text-yellow-700">
                  {e}
                </p>
              ))}
            </section>

            <section className="rounded border p-4">
              <h2 className="mb-2 font-semibold">
                4. Tokens, cost and time
              </h2>

              <dl className="grid grid-cols-2 gap-2 text-sm">
                <Row k="Model" v={out.model} />
                <Row k="Prompt version" v={out.prompt_version} />
                <Row k="Input tokens" v={out.input_tokens} />
                <Row k="Output tokens" v={out.output_tokens} />
                <Row k="Cost (USD)" v={out.cost?.total_cost?.toFixed(6)} />
                <Row k="Would-be paid cost (USD)" v={out.cost?.would_be_cost?.toFixed(6)} />
                <Row k="Duration (s)" v={out.duration} />
                <Row k="LLM attempts" v={out.attempts} />
                <Row k="Total cost, all runs (USD)" v={stats?.total_cost?.toFixed(6)} />
                <Row k="Total runs" v={stats?.runs} />
              </dl>
            </section>
          </div>

          {r ? (
            <>
              <section className="rounded border p-4">
                <h2 className="mb-2 font-semibold">
                  5. Parsed information
                </h2>

                <dl className="grid grid-cols-2 gap-3 text-sm md:grid-cols-3">
                  <Row k="Name" v={r.name} />
                  <Row k="Emails" v={r.email_addresses} />
                  <Row k="Phones" v={r.phone_numbers} />
                  <Row k="LinkedIn" v={r.linkedin_url} />
                  <Row k="Address" v={r.address} />
                  <Row k="Years of experience" v={r.years_of_experience} />
                  <Row k="Last company" v={r.last_working_company} />
                  <Row k="Skills" v={r.skills} />
                  <Row k="Certifications" v={r.certifications} />
                  <Row k="Languages" v={r.languages} />
                </dl>

                <h3 className="mt-4 font-medium">Experience</h3>

                <ul className="list-disc pl-5 text-sm">
                  {r.experience?.map((e: any, i: number) => (
                    <li key={i}>
                      {e.title} at {e.company} ({e.start_date} to {e.end_date})
                    </li>
                  ))}
                </ul>
              </section>

              <section className="rounded border p-4">
                <h2 className="mb-2 font-semibold">6. JSON output</h2>

                <pre className="max-h-96 overflow-auto rounded bg-gray-900 p-4 text-xs text-green-200">
                  {JSON.stringify(r, null, 2)}
                </pre>
              </section>
            </>
          ) : (
            <p className="text-red-600">Parsing failed: {out.error}</p>
          )}
        </>
      )}
    </main>
  );
}

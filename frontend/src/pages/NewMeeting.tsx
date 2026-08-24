import React, { useState, useEffect } from 'react';
import { Upload, FileText, Mic, HardDrive, AlertCircle, Loader2, CheckCircle2, XCircle } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

type QueueItem = {
  id: string; // temp id for UI until we get meeting_id
  file: File;
  status: 'queued' | 'uploading' | 'processing' | 'needs_review' | 'completed' | 'failed';
  meeting_id?: string;
  error?: string;
};

export default function NewMeeting() {
  const [mode, setMode] = useState<'upload' | 'paste' | 'audio' | 'drive'>('upload');
  const [transcript, setTranscript] = useState('');
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const navigate = useNavigate();

  // Poll for status updates
  useEffect(() => {
    const activeItems = queue.filter(q => q.status === 'processing');
    if (activeItems.length === 0) return;

    const interval = setInterval(async () => {
      let updatedQueue = [...queue];
      let changed = false;

      for (const item of activeItems) {
        if (!item.meeting_id) continue;
        try {
          const res = await fetch(`/api/meetings/${item.meeting_id}`);
          if (res.ok) {
            const data = await res.json();
            const newStatus = data.processing_status;
            let uiStatus = item.status;
            if (newStatus === 'completed') uiStatus = 'completed';
            if (newStatus === 'failed') uiStatus = 'failed';
            if (newStatus === 'needs_approval' || newStatus === 'needs_clarification') uiStatus = 'needs_review';
            
            if (uiStatus !== item.status) {
              const idx = updatedQueue.findIndex(q => q.id === item.id);
              if (idx > -1) {
                updatedQueue[idx] = { ...updatedQueue[idx], status: uiStatus };
                changed = true;
              }
            }
          }
        } catch (e) {
          console.error(e);
        }
      }

      if (changed) {
        setQueue(updatedQueue);
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [queue]);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    if (files.length === 0) return;

    const newItems: QueueItem[] = files.map(f => ({
      id: Math.random().toString(36).substr(2, 9),
      file: f,
      status: 'queued'
    }));

    setQueue(prev => [...prev, ...newItems]);
    
    // Process them
    for (const item of newItems) {
      setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'uploading' } : q));
      try {
        const text = await item.file.text();
        const res = await fetch('/api/meetings/bulk_extract', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ meetings: [{ transcript: text, roster_names: [] }] })
        });
        
        if (!res.ok) throw new Error('Upload failed');
        const data = await res.json();
        const meeting_id = data.meeting_ids[0];
        
        setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'processing', meeting_id } : q));
      } catch (err: any) {
        setQueue(prev => prev.map(q => q.id === item.id ? { ...q, status: 'failed', error: err.message } : q));
      }
    }
  };

  const completedCount = queue.filter(q => q.status === 'completed' || q.status === 'needs_review' || q.status === 'failed').length;

  return (
    <div className="p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-semibold text-gray-900 tracking-tight">New Meeting</h1>
        <p className="text-gray-500 mt-1 text-sm">Add meetings to organizational memory to extract decisions and commitments.</p>
      </div>

      {queue.length > 0 ? (
        <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h3 className="text-sm font-semibold text-gray-900 uppercase tracking-wider">Importing Meetings</h3>
            <p className="text-xs text-gray-500 mt-1">{queue.length} files selected</p>
          </div>
          <ul className="divide-y divide-gray-200">
            {queue.map(q => (
              <li key={q.id} className="px-6 py-4 flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  {q.status === 'completed' && <CheckCircle2 className="w-5 h-5 text-green-500" />}
                  {q.status === 'failed' && <XCircle className="w-5 h-5 text-red-500" />}
                  {q.status === 'needs_review' && <AlertCircle className="w-5 h-5 text-amber-500" />}
                  {(q.status === 'queued' || q.status === 'uploading' || q.status === 'processing') && <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />}
                  <span className="text-sm font-medium text-gray-900">{q.file.name}</span>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="text-sm text-gray-500 capitalize">
                    {q.status.replace('_', ' ')}
                  </span>
                  {q.status === 'needs_review' && (
                    <button onClick={() => navigate('/decisions/inbox')} className="text-xs font-medium text-white bg-amber-600 px-3 py-1.5 rounded hover:bg-amber-700">
                      Review
                    </button>
                  )}
                  {(q.status === 'completed' || q.status === 'failed' || q.status === 'needs_review') && q.meeting_id && (
                    <button onClick={() => navigate('/meetings')} className="text-xs font-medium text-gray-700 bg-gray-100 px-3 py-1.5 rounded hover:bg-gray-200">
                      View
                    </button>
                  )}
                </div>
              </li>
            ))}
          </ul>
          <div className="px-6 py-3 bg-gray-50 border-t border-gray-200 text-xs text-gray-500 font-medium">
            {completedCount} / {queue.length} completed
          </div>
        </div>
      ) : (
        <>
          <div className="flex space-x-4 mb-8">
            {[
              { id: 'upload', icon: FileText, label: 'Upload Transcript' },
              { id: 'paste', icon: FileText, label: 'Paste Text' },
              { id: 'audio', icon: Mic, label: 'Upload Audio/Video' },
              { id: 'drive', icon: HardDrive, label: 'Google Drive' }
            ].map(m => (
              <button
                key={m.id}
                onClick={() => setMode(m.id as any)}
                className={`flex-1 py-4 px-4 flex flex-col items-center justify-center border rounded-lg transition-colors ${
                  mode === m.id ? 'border-blue-600 bg-blue-50 text-blue-700' : 'border-gray-200 bg-white text-gray-600 hover:bg-gray-50'
                }`}
              >
                <m.icon className="w-6 h-6 mb-2" />
                <span className="text-sm font-medium">{m.label}</span>
              </button>
            ))}
          </div>

          <div className="bg-white rounded-lg border border-gray-200 shadow-sm p-6">
            {mode === 'upload' && (
              <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg bg-gray-50 hover:bg-gray-100 transition-colors">
                <Upload className="w-10 h-10 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-1">Upload meeting transcripts</h3>
                <p className="text-sm text-gray-500 mb-4">Supports multiple .txt, .md, .vtt, .srt up to 10MB each</p>
                <label className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 cursor-pointer shadow-sm">
                  Select Files
                  <input type="file" multiple className="hidden" accept=".txt,.md,.vtt,.srt" onChange={handleFileUpload} />
                </label>
              </div>
            )}

            {mode === 'paste' && (
              <div>
                <textarea
                  className="w-full h-64 p-4 border border-gray-300 rounded-md shadow-sm focus:ring-blue-500 focus:border-blue-500 sm:text-sm text-gray-900 font-mono"
                  placeholder="Paste meeting transcript here..."
                  value={transcript}
                  onChange={e => setTranscript(e.target.value)}
                />
                <div className="mt-4 flex justify-end">
                  <button
                    disabled={!transcript.trim()}
                    onClick={() => {
                      const file = new File([transcript], 'pasted_transcript.txt', { type: 'text/plain' });
                      handleFileUpload({ target: { files: [file] } } as any);
                    }}
                    className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 shadow-sm"
                  >
                    Analyze Transcript
                  </button>
                </div>
              </div>
            )}

            {(mode === 'audio' || mode === 'drive') && (
              <div className="text-center py-12">
                <div className="bg-amber-50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4 border border-amber-100">
                  <AlertCircle className="w-8 h-8 text-amber-600" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">Integration Not Configured</h3>
                <p className="text-sm text-gray-500 max-w-sm mx-auto mb-6">
                  {mode === 'audio' 
                    ? "The audio transcription provider is not currently configured for this environment."
                    : "Google Drive OAuth has not been connected to this workspace."}
                </p>
                <button
                  onClick={() => setMode('upload')}
                  className="inline-flex items-center px-4 py-2 border border-gray-300 shadow-sm text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 transition-colors"
                >
                  Upload Transcript Instead
                </button>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

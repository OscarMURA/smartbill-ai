import { useRef, useState } from 'react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { AlertCircle, CheckCircle2, FileUp, LoaderCircle, LockKeyhole, ShieldCheck, X } from 'lucide-react';
import { ApiRequestError, uploadInvoice } from '../lib/api';
import type { InvoiceOut } from '../types/api';
import { Badge } from './ui/badge';
import { Button } from './ui/button';
import { Card } from './ui/card';

const MAX_FILE_SIZE = 10 * 1024 * 1024;

export default function InvoiceUploader({ onComplete, collectionId }: { onComplete: (invoice: InvoiceOut) => void; collectionId?: string }) {
  const inputRef = useRef<HTMLInputElement>(null);
  const queryClient = useQueryClient();
  const [dragging, setDragging] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState('');
  const mutation = useMutation({
    mutationFn: (file: File) => uploadInvoice(file, collectionId),
    onSuccess: async invoice => {
      await queryClient.invalidateQueries({ queryKey: ['dashboard'] });
      await queryClient.invalidateQueries({ queryKey: ['invoice', invoice.id] });
      onComplete(invoice);
    },
  });

  const choose = (candidate?: File) => {
    if (!candidate) return;
    mutation.reset();
    setValidationError('');
    if (!candidate.name.toLowerCase().endsWith('.pdf') || (candidate.type && candidate.type !== 'application/pdf')) {
      setFile(null); setValidationError('Selecciona un archivo PDF.'); return;
    }
    if (candidate.size > MAX_FILE_SIZE) {
      setFile(null); setValidationError('El archivo supera el límite de 10 MB. Elige un PDF más pequeño.'); return;
    }
    setFile(candidate);
  };

  const onDrop = (event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault(); setDragging(false); choose(event.dataTransfer.files[0]);
  };

  return <Card className="upload-card panel" role="region" aria-labelledby="upload-title">
    <div className="upload-heading"><div className="upload-icon"><FileUp size={19}/></div><div><h2 id="upload-title">Añadir una factura</h2><p>Extraemos solo los datos necesarios para tu análisis.</p></div></div>
    <div className={`drop-zone ${dragging ? 'dragging' : ''} ${validationError || mutation.isError ? 'drop-error' : ''}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={event => { if (!event.currentTarget.contains(event.relatedTarget as Node)) setDragging(false); }} onDrop={onDrop}>
      <input ref={inputRef} className="sr-only" type="file" accept="application/pdf,.pdf" aria-label="Seleccionar factura en formato PDF" onChange={event => choose(event.currentTarget.files?.[0])}/>
      <span className="drop-icon"><FileUp size={21}/></span>
      <strong>Arrastra tu factura aquí</strong>
      <span className="drop-hint">o <button type="button" className="inline-link" onClick={() => inputRef.current?.click()}>selecciona un archivo</button></span>
      <span className="file-limits">PDF · máximo 10 MB</span>
    </div>
    {(validationError || mutation.isError) && <div className="upload-feedback feedback-error" role="alert"><AlertCircle size={16}/><span>{validationError || (mutation.error instanceof ApiRequestError ? mutation.error.message : 'No se pudo procesar el archivo.')}</span></div>}
    {mutation.isSuccess && <div className="upload-feedback feedback-success" role="status"><CheckCircle2 size={16}/><span>Factura procesada. Ya puedes revisar los campos extraídos y sus advertencias.</span></div>}
    {file && <div className="selected-file"><span className="selected-file-icon"><FileUp size={16}/></span><span className="selected-file-copy"><strong>{file.name}</strong><small>{(file.size / 1024 / 1024).toFixed(2)} MB</small></span><Badge variant="outline" className="file-type-badge">PDF</Badge><button type="button" className="icon-button" aria-label="Quitar archivo seleccionado" onClick={() => { setFile(null); if (inputRef.current) inputRef.current.value = ''; }}><X size={16}/></button></div>}
    <Button type="button" className="button button-primary upload-submit" disabled={!file || mutation.isPending} onClick={() => file && mutation.mutate(file)}>{mutation.isPending ? <><LoaderCircle size={16} className="spin"/> Procesando factura…</> : <><FileUp size={16}/> Procesar factura</>}</Button>
    <div className="privacy-promise"><ShieldCheck size={15}/><span>PDF temporal. No guardamos el archivo original.</span><LockKeyhole size={14}/></div>
  </Card>;
}

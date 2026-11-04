import { requireUuid } from './ids.mjs';
export class ApiError extends Error {
  constructor(message, status = 0, code = 'REQUEST_FAILED') { super(message); this.status = status; this.code = code; }
}
export const LIVE_API_BASE='https://gnlnv6dd5j.execute-api.eu-north-1.amazonaws.com';
export const STORAGE_ORIGIN='https://s3.eu-north-1.amazonaws.com';
const transient = status => status === 429 || status === 408 || status >= 500;
export class ApiClient {
  constructor(config, role = 'student', fetcher = fetch, { getAccessToken, sleep = ms => new Promise(r => setTimeout(r, ms)), onProgress = () => {} } = {}) {
    this.config = config; this.role = role; this.fetcher = fetcher.bind(globalThis);
    this.getAccessToken = getAccessToken; this.sleep = sleep; this.onProgress = onProgress;
    this.origin = globalThis.location?.origin ?? 'http://localhost';
    if (!['demo', 'live'].includes(config.mode)) throw Error('mode must be demo or live');
    const base = new URL(config.apiBase, this.origin);
    if (base.search || base.hash || base.username || base.password) throw Error('Invalid API base URL');
    if (config.mode === 'live' && base.protocol !== 'https:' && base.origin !== this.origin) throw Error('Live API must use HTTPS');
    this.base = base.href.replace(/\/$/, '');
  }
  async request(path, { method = 'GET', body, key } = {}) {
    let refreshed = false, forceRefresh=false;
    for (let attempt = 0; ; attempt++) {
      const headers = { Accept: 'application/json' };
      if (body !== undefined) headers['Content-Type'] = 'application/json';
      if (key) headers['Idempotency-Key'] = requireUuid(key, 'Idempotency key');
      if (this.config.mode === 'demo') headers['X-Demo-Role'] = this.role;
      else {
        const token = await this.getAccessToken?.({ forceRefresh });
        if (!token || typeof token !== 'string') throw new ApiError('Sign in before accessing the proctoring API', 401, 'SIGN_IN_REQUIRED');
        headers.Authorization = `Bearer ${token}`;forceRefresh=false;
      }
      let response;
      try {
        response = await this.fetcher(`${this.base}${path}`, { method, headers, credentials: 'omit', redirect: 'error',
          signal: AbortSignal.timeout(20000), ...(body === undefined ? {} : { body: JSON.stringify(body) }) });
      } catch {
        if (attempt < 2 && (method === 'GET' || key)) { await this.backoff(attempt, 'API network retry'); continue; }
        throw new ApiError('API could not be reached. The clip can be retried while this page stays open.');
      }
      if (response.status === 401 && this.config.mode === 'live' && !refreshed) { refreshed = true;forceRefresh=true; continue; }
      if (!response.ok) {
        if (transient(response.status) && attempt < 2 && (method === 'GET' || key)) { await this.backoff(attempt, 'API retry'); continue; }
        const detail = await response.json().catch(() => ({}));
        throw new ApiError(typeof detail.error==='string' ? detail.error : `Request failed: HTTP ${response.status}`, response.status);
      }
      return response.status === 204 ? null : response.json();
    }
  }
  async backoff(attempt, phase) { this.onProgress({ phase, attempt: attempt + 1 }); await this.sleep(Math.min(4000, 400 * 2 ** attempt)); }
  storageUrl(value, allowlist, purpose) {
    const target = new URL(value, this.origin);
    if (target.username || target.password || target.hash) throw Error(`Invalid ${purpose} URL`);
    const local = this.config.mode === 'demo' && target.origin === this.origin;
    if (!local && (target.protocol !== 'https:' || !allowlist?.includes(target.origin))) throw Error(`${purpose} destination not allowlisted`);
    return target.href;
  }
  async submit(event, blob) {
    requireUuid(event.eventId, 'Event ID'); requireUuid(event.examId, 'Exam ID');
    if (this.config.mode==='live' && event.synthetic!==false) throw Error('Synthetic events are demo-only');
    if (blob.size < 1 || blob.size > 20 * 1024 * 1024) throw Error('Clip size must be between 1 byte and 20 MiB');
    const contentType=blob.type.toLowerCase();
    if (!/^video\/webm(;codecs=vp[89])?$/.test(contentType)) throw Error('This integration accepts video/webm only');
    const started=performance.now();let ticket,uploaded=false;
    for(let attempt=0;attempt<3;attempt++) {
      this.onProgress({phase:'requesting-upload',attempt:attempt+1});
      ticket=await this.request('/clips/presign',{method:'POST',key:event.eventId,body:{eventId:event.eventId,examId:event.examId,contentType}});
      if(!ticket || typeof ticket.objectKey!=='string' || !ticket.fields || typeof ticket.fields!=='object' || Array.isArray(ticket.fields) || !Number.isInteger(ticket.maxBytes) || blob.size>ticket.maxBytes)throw Error('Invalid upload ticket or clip exceeds ticket limit');
      if(ticket.fields['Content-Type']!==contentType || ticket.fields.key!==ticket.objectKey || Object.hasOwn(ticket.fields,'file') || Object.values(ticket.fields).some(v=>typeof v!=='string'))throw Error('Invalid signed POST fields');
      const target=this.storageUrl(ticket.uploadUrl,this.config.uploadOrigins??[STORAGE_ORIGIN],'Upload');
      const form=new FormData();for(const [name,value]of Object.entries(ticket.fields))form.append(name,value);
      form.append('file',blob,`${event.eventId}.webm`); // S3 requires the file field last.
      this.onProgress({phase:'uploading',attempt:attempt+1});
      try {
        const response=await this.fetcher(target,{method:'POST',body:form,credentials:'omit',redirect:'error',signal:AbortSignal.timeout(60000)});
        if(response.status===204){uploaded=true;break;}
        const expired=response.status===403 && /Policy expired/i.test(await response.text());
        if(!expired && !transient(response.status))throw new ApiError(`Clip upload failed: HTTP ${response.status}`,response.status);
      }catch(error){if(error instanceof ApiError)throw error;}
      if(attempt<2)await this.backoff(attempt,'Renewing upload ticket');
    }
    if(!uploaded)throw new ApiError('Clip upload failed after three attempts. Keep this page open and retry.');
    this.onProgress({phase:'logging-event'});
    const {event:saved}=await this.request('/events',{method:'POST',key:event.eventId,body:{...event,objectKey:ticket.objectKey,contentType,sizeBytes:blob.size}});
    if(!saved || saved.eventId!==event.eventId)throw Error('Invalid event response');
    this.onProgress({phase:'complete',elapsedMs:performance.now()-started});return saved;
  }
  policy() { return this.request('/policy'); }
  list(examId, cursor = null) {
    requireUuid(examId, 'Exam ID');
    return this.request(`/events?examId=${encodeURIComponent(examId)}${cursor ? `&cursor=${encodeURIComponent(cursor)}` : ''}`);
  }
  review(eventId, decision, version) {
    requireUuid(eventId, 'Event ID');
    if (!['confirmed', 'dismissed'].includes(decision) || !Number.isInteger(version) || version < 0) throw Error('Invalid review');
    return this.request(`/events/${eventId}/review`, { method: 'PATCH', body: { decision, version } });
  }
  async playback(eventId) {
    requireUuid(eventId, 'Event ID'); const { url } = await this.request(`/events/${eventId}/playback`);
    return this.storageUrl(url, this.config.playbackOrigins, 'Playback');
  }
}

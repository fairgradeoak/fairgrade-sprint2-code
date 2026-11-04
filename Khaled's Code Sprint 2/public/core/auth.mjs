const b64url = bytes => btoa(String.fromCharCode(...bytes)).replaceAll('+','-').replaceAll('/','_').replace(/=+$/, '');
export class CognitoSession {
  constructor(config, fetcher = fetch) { this.config = config; this.fetcher = fetcher.bind(globalThis); this.tokens = null; this.refreshing = null; }
  settings() {
    const c = this.config.auth;
    if (!c?.domain || !c?.clientId || !c?.redirectUri) throw Error('Configure the Cognito public app client, domain and redirect URI first');
    const domain = new URL(c.domain), redirect = new URL(c.redirectUri);
    if (domain.protocol !== 'https:' || domain.pathname !== '/' || domain.search || domain.hash || domain.username) throw Error('Cognito domain must be an HTTPS origin');
    if (redirect.origin !== location.origin || redirect.pathname !== location.pathname || redirect.search || redirect.hash) throw Error('Cognito redirect URI must match this page and be registered in the app client');
    return c;
  }
  async signIn() {
    const c = this.settings(), verifier = b64url(crypto.getRandomValues(new Uint8Array(48))), state = b64url(crypto.getRandomValues(new Uint8Array(32)));
    const challenge = b64url(new Uint8Array(await crypto.subtle.digest('SHA-256', new TextEncoder().encode(verifier))));
    sessionStorage.setItem('fairgrade-oauth-transaction', JSON.stringify({ verifier, state, createdAt: Date.now(), redirectUri: c.redirectUri }));
    const url = new URL('/oauth2/authorize', c.domain);
    url.search = new URLSearchParams({ response_type: 'code', client_id: c.clientId, redirect_uri: c.redirectUri,
      scope: (c.scopes || ['openid']).join(' '), state, code_challenge: challenge, code_challenge_method: 'S256' }).toString();
    location.assign(url.href);
  }
  async initialize() {
    const params = new URLSearchParams(location.search);
    if (!params.has('code') && !params.has('error')) return;
    const c = this.settings(); const transaction = JSON.parse(sessionStorage.getItem('fairgrade-oauth-transaction') || 'null');
    sessionStorage.removeItem('fairgrade-oauth-transaction'); history.replaceState(null, '', location.pathname);
    if (!transaction || params.get('state') !== transaction.state || !Number.isFinite(transaction.createdAt) || transaction.createdAt > Date.now() || Date.now() - transaction.createdAt > 600000 || transaction.redirectUri !== c.redirectUri) throw Error('Invalid or expired sign-in transaction');
    if (params.has('error')) throw Error('Cognito sign-in was not completed');
    await this.exchange({ grant_type: 'authorization_code', code: params.get('code'), code_verifier: transaction.verifier, redirect_uri: c.redirectUri });
  }
  async exchange(fields) {
    const c = this.settings();
    const response = await this.fetcher(new URL('/oauth2/token', c.domain), { method:'POST', credentials:'omit', redirect:'error',
      headers:{'Content-Type':'application/x-www-form-urlencoded'}, body:new URLSearchParams({ client_id:c.clientId, ...fields }), signal:AbortSignal.timeout(20000) });
    if (!response.ok) { this.tokens = null; throw Error('Sign-in expired or failed. Sign in again.'); }
    const value = await response.json();
    if (typeof value.access_token!=='string' || !value.access_token || !Number.isFinite(value.expires_in) || value.expires_in<=0) throw Error('Invalid Cognito token response');
    this.tokens = { access: value.access_token, refresh: value.refresh_token || this.tokens?.refresh, expiresAt: Date.now() + value.expires_in * 1000 };
  }
  async getAccessToken({ forceRefresh = false } = {}) {
    if (!this.tokens) return null;
    if (forceRefresh || this.tokens.expiresAt - Date.now() < 60000) {
      if (!this.tokens.refresh) { this.tokens = null; return null; }
      if (!this.refreshing) this.refreshing = this.exchange({ grant_type:'refresh_token', refresh_token:this.tokens.refresh }).finally(() => { this.refreshing = null; });
      await this.refreshing;
    }
    return this.tokens?.access;
  }
  signOut() {
    this.tokens = null; sessionStorage.removeItem('fairgrade-oauth-transaction');
    const c = this.settings(); const url = new URL('/logout', c.domain);
    url.search = new URLSearchParams({ client_id:c.clientId, logout_uri:c.redirectUri }).toString(); location.assign(url.href);
  }
}
export async function mountAuth(config, root) {
  if (config.mode === 'demo') { root.hidden = true; return { getAccessToken: async () => null }; }
  config.auth = { ...config.auth, redirectUri: config.auth?.redirectUris?.[location.pathname] || config.auth?.redirectUri };
  const session = new CognitoSession(config);
  const status = document.createElement('span'), login = document.createElement('button'), logout = document.createElement('button');
  login.textContent = 'Sign in'; logout.textContent = 'Sign out'; logout.className = 'secondary'; root.replaceChildren(status, login, logout);
  try { await session.initialize(); status.textContent = session.tokens ? 'Signed in for this page. ' : 'Sign in to use your exam account. '; }
  catch (e) { status.textContent = e.message; }
  login.onclick = () => session.signIn().catch(e => { status.textContent = e.message; });
  logout.onclick = () => { try { session.signOut(); } catch (e) { status.textContent = e.message; } };
  return { getAccessToken: options => session.getAccessToken(options) };
}

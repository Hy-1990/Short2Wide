(()=>{
  const svg=(path)=>`<svg viewBox="0 0 24 24" aria-hidden="true">${path}</svg>`;
  const icons={sun:svg('<circle cx="12" cy="12" r="4"/><path d="M12 2v2m0 16v2M2 12h2m16 0h2M5 5l1.5 1.5m11 11L19 19M5 19l1.5-1.5m11-11L19 5"/>'),moon:svg('<path d="M20 14.5A8.5 8.5 0 0 1 9.5 4 8.5 8.5 0 1 0 20 14.5Z"/>'),key:svg('<circle cx="8" cy="9" r="4"/><path d="m11 12 8 8m-3-3 3-3m-6 0 3-3"/>'),close:svg('<path d="m6 6 12 12M18 6 6 18"/>'),eye:svg('<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>')};
  const t=window.reframeI18n.t;
  const read=(key,fallback)=>{try{return localStorage.getItem(key)||fallback}catch{return fallback}};
  const write=(key,value)=>{try{localStorage.setItem(key,value)}catch{}};
  let theme=read('reframe-theme','system');if(!['system','light','dark'].includes(theme))theme='system';
  const system=matchMedia('(prefers-color-scheme: dark)');
  const dialog=document.createElement('dialog');dialog.id='settings-dialog';dialog.setAttribute('aria-labelledby','settings-title');
  dialog.innerHTML=`<div class="dialog-heading"><h2 id="settings-title">偏好设置</h2><button type="button" class="icon-button settings-close" aria-label="关闭设置">${icons.close}</button></div><div class="settings-row"><span>外观</span><div class="settings-segments" role="group" aria-label="外观"><button type="button" data-theme-choice="light">浅色</button><button type="button" data-theme-choice="dark">深色</button><button type="button" data-theme-choice="system">跟随系统</button></div></div><div class="settings-row"><span>语言</span><div class="settings-segments" role="group" aria-label="语言"><button type="button" data-language-choice="zh">中文</button><button type="button" data-language-choice="en">English</button></div></div><form class="key-section" id="key-form"><div class="key-heading"><label for="dreamapi-key">DreamAPI 密钥</label><a href="https://api.newportai.com/" target="_blank" rel="noopener noreferrer">获取密钥 ↗</a></div><div class="key-input-wrap"><input type="password" id="dreamapi-key" placeholder="输入 API Key" autocomplete="off" spellcheck="false" aria-describedby="key-note key-state"><button type="button" id="toggle-key" aria-label="显示密钥" aria-pressed="false">${icons.eye}</button></div><p class="key-note" id="key-note">仅保存在本机服务，不写入浏览器。保存不代表连接验证成功。</p><p class="key-state" id="key-state" role="status" aria-live="polite"></p><div class="key-actions"><button type="button" class="clear-key" id="clear-key" disabled>清除密钥</button><button type="submit" class="button button-primary" id="save-key">保存密钥</button></div></form>`;
  document.body.append(dialog);
  document.querySelectorAll('[data-app-controls]').forEach(slot=>{
    slot.className='app-controls';
    slot.innerHTML=`<button class="control-button control-theme" type="button" aria-label="切换明暗模式"></button><button class="control-button control-language" type="button" aria-label="切换语言">EN</button><button class="control-button control-key" type="button" aria-label="DreamAPI 设置">${icons.key}<span class="key-label">DreamAPI</span><span class="key-dot" aria-hidden="true"></span></button>`;
  });
  const input=dialog.querySelector('#dreamapi-key'),state=dialog.querySelector('#key-state'),save=dialog.querySelector('#save-key'),clear=dialog.querySelector('#clear-key');
  let configured=false,busy=false,opener;
  function message(text,kind=''){state.textContent=t(text);state.dataset.state=kind;if(kind==='error'||kind==='success')window.reframeUI?.toast(text,kind)}
  function configState(value){configured=value;clear.disabled=!value||busy;document.querySelectorAll('.key-dot').forEach(dot=>dot.classList.toggle('configured',value));input.placeholder=t(value?'已保存 · 输入新密钥以替换':'输入 API Key')}
  function applyPreferences(){
    const resolved=theme==='system'?(system.matches?'dark':'light'):theme;
    document.documentElement.dataset.theme=resolved;
    document.querySelector('meta[name="theme-color"]')?.setAttribute('content',resolved==='dark'?'#151714':'#f7f7f2');
    document.querySelectorAll('.control-theme').forEach(b=>{b.innerHTML=resolved==='dark'?icons.sun:icons.moon;b.setAttribute('aria-label',t(resolved==='dark'?'切换浅色模式':'切换深色模式'));b.title=b.getAttribute('aria-label')});
    document.querySelectorAll('.control-language').forEach(b=>{b.textContent=window.reframeI18n.language()==='en'?'中':'EN';b.setAttribute('aria-label',window.reframeI18n.language()==='en'?'Switch to Chinese':'Switch to English')});
    dialog.querySelectorAll('[data-theme-choice]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.themeChoice===theme)));
    dialog.querySelectorAll('[data-language-choice]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.languageChoice===window.reframeI18n.language())));
  }
  function setTheme(value){theme=value;write('reframe-theme',value);applyPreferences()}
  dialog.querySelectorAll('[data-theme-choice]').forEach(b=>b.onclick=()=>setTheme(b.dataset.themeChoice));
  dialog.querySelectorAll('[data-language-choice]').forEach(b=>b.onclick=()=>window.reframeI18n.setLanguage(b.dataset.languageChoice));
  document.querySelectorAll('.control-theme').forEach(b=>b.onclick=()=>setTheme(document.documentElement.dataset.theme==='dark'?'light':'dark'));
  document.querySelectorAll('.control-language').forEach(b=>b.onclick=()=>window.reframeI18n.setLanguage(window.reframeI18n.language()==='en'?'zh':'en'));
  async function loadState(){
    try{const r=await fetch('/api/settings/dreamapi',{cache:'no-store'});if(!r.ok)throw Error();const data=await r.json();configState(data.configured);if(dialog.open)message(data.configured?'密钥已保存 · 尚未验证':'尚未配置密钥')}
    catch{if(dialog.open)message('本机设置服务不可用，请使用项目启动命令重启。','error')}
  }
  document.querySelectorAll('.control-key').forEach(b=>b.onclick=()=>{opener=b;input.value='';input.type='password';dialog.querySelector('#toggle-key').setAttribute('aria-pressed','false');dialog.querySelector('#toggle-key').setAttribute('aria-label',t('显示密钥'));message('读取设置…');dialog.showModal();loadState()});
  dialog.querySelector('.settings-close').onclick=()=>dialog.close();
  dialog.addEventListener('close',()=>{input.value='';opener?.focus()});
  dialog.addEventListener('click',e=>{if(e.target!==dialog)return;const r=dialog.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)dialog.close()});
  dialog.querySelector('#toggle-key').onclick=e=>{const show=input.type==='password';input.type=show?'text':'password';e.currentTarget.setAttribute('aria-pressed',String(show));e.currentTarget.setAttribute('aria-label',t(show?'隐藏密钥':'显示密钥'))};
  async function changeKey(method,key){
    if(busy)return;
    busy=true;save.disabled=true;clear.disabled=true;message('保存中…');
    try{const r=await fetch('/api/settings/dreamapi',{method,headers:{'Content-Type':'application/json'},...(method==='POST'?{body:JSON.stringify({key})}:{})});if(!r.ok)throw Error(r.status===400?'invalid':'service');const data=await r.json();input.value='';configState(data.configured);message(data.configured?'密钥已保存 · 尚未验证':'密钥已清除','success')}
    catch(error){message(error.message==='invalid'?'密钥格式不正确，请检查后重试。':'保存失败，请检查本机设置服务后重试。','error')}
    finally{busy=false;save.disabled=false;clear.disabled=!configured}
  }
  dialog.querySelector('#key-form').onsubmit=e=>{e.preventDefault();const key=input.value.trim();if(!key){message('请先输入密钥。','error');input.focus();return}changeKey('POST',key)};
  clear.onclick=()=>changeKey('DELETE');
  document.addEventListener('reframe-language',()=>{applyPreferences();configState(configured)});
  system.addEventListener('change',()=>{if(theme==='system')applyPreferences()});
  applyPreferences();window.reframeI18n.translate(dialog);loadState();
})();

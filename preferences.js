// Apply before the styles load to avoid a flash of the wrong theme.
(()=>{
  let theme='system',language='zh';
  try{theme=localStorage.getItem('reframe-theme')||theme;language=localStorage.getItem('reframe-language')||language}catch{}
  if(!['system','light','dark'].includes(theme))theme='system';
  document.documentElement.dataset.theme=theme==='system'?(matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'):theme;
  document.documentElement.lang=language==='en'?'en':'zh-CN';
})();

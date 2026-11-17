const form=document.querySelector('#import-video');
const source=document.querySelector('#home-source');
const file=document.querySelector('#home-file');
const error=document.querySelector('#import-error');
let ratio='16:9';
let importing=false,importStarted=0,importEpoch=0;
function resetImport(){importing=false;const button=form.querySelector('[type="submit"]');button.disabled=false;button.classList.remove('is-working');button.querySelector('span').textContent=window.reframeI18n.t('开始改编');form.removeAttribute('aria-busy');document.querySelector('#import-help').textContent=window.reframeI18n.t('支持小于5分钟的视频')}
setInterval(()=>{if(importing){const elapsed=Math.floor((Date.now()-importStarted)/1000);document.querySelector('#import-help').textContent=window.reframeI18n.language()==='en'?`Importing · ${elapsed}s elapsed`:`正在导入 · 已用时 ${elapsed} 秒`}},1000);
document.querySelectorAll('[data-home-ratio]').forEach(button=>button.addEventListener('click',()=>{
  ratio=button.dataset.homeRatio;
  document.querySelectorAll('[data-home-ratio]').forEach(item=>{item.classList.toggle('active',item===button);item.setAttribute('aria-pressed',String(item===button))});
}));
document.querySelector('#home-upload').addEventListener('click',()=>file.click());
file.addEventListener('change',()=>{document.querySelector('#home-file-name').textContent=file.files[0]?.name||window.reframeI18n.t('上传视频');error.hidden=true;source.removeAttribute('aria-invalid')});
source.addEventListener('input',()=>{error.hidden=true;source.removeAttribute('aria-invalid')});
window.reframeI18n.addMessages({'支持小于5分钟的视频':'Videos under 5 minutes','正在导入…':'Importing…','上传或下载失败，请重试。':'Import failed. Please retry.','最近项目':'Recent projects','查看示例':'View example','粘贴链接或上传小于5分钟的视频，选择目标画幅。按画面变化与停顿分段，逐段生成并核对，最后合成导出。':'Add a video under five minutes and choose an aspect ratio. Split on scene changes and pauses, generate and review each segment, then export.'});
form.addEventListener('submit',async event=>{
  event.preventDefault();
  const link=source.value.trim();
  if(!link&&!file.files.length){window.reframeUI.toast('请先粘贴视频链接，或选择一个本地视频。','error');error.textContent='请先粘贴视频链接，或选择一个本地视频。';error.hidden=false;source.setAttribute('aria-invalid','true');source.focus();return}
  if(link){
    let valid=false;
    try{const url=new URL(link);const host=url.hostname;valid=url.protocol==='https:'&&(['youtube.com','youtu.be','tiktok.com'].includes(host)||host.endsWith('.youtube.com')||host.endsWith('.tiktok.com'))}catch{}
    if(!valid){window.reframeUI.toast('请使用有效的 YouTube 或 TikTok 视频链接，或清空链接后选择本地视频。','error');error.textContent='请使用有效的 YouTube 或 TikTok 视频链接，或清空链接后选择本地视频。';error.hidden=false;source.setAttribute('aria-invalid','true');source.focus();return}
  }
  const button=form.querySelector('[type="submit"]');
  if(importing)return;const ticket=++importEpoch;importing=true;importStarted=Date.now();button.classList.add('is-working');form.setAttribute('aria-busy','true');
  button.disabled=true;button.querySelector('span').textContent=window.reframeI18n.t('正在导入…');
  try{
    let response;
    if(link)response=await fetch('/api/projects/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({url:link,ratio})});
    else response=await fetch(`/api/projects/upload?ratio=${encodeURIComponent(ratio)}&name=${encodeURIComponent(file.files[0].name)}`,{method:'POST',headers:{'Content-Type':'application/octet-stream'},body:file.files[0]});
    const data=await response.json();if(!response.ok)throw Error(data.error||'上传或下载失败，请重试。');
    if(ticket!==importEpoch)return;window.location.href=`project.html?id=${data.id}`;
  }catch(problem){importing=false;button.classList.remove('is-working');form.removeAttribute('aria-busy');document.querySelector('#import-help').textContent=window.reframeI18n.t('支持小于5分钟的视频');error.textContent=window.reframeUI.message(problem);window.reframeUI.toast(error.textContent,'error');error.hidden=false;button.disabled=false;button.querySelector('span').textContent=window.reframeI18n.t('开始改编')}

});


window.reframeI18n.addMessages({'新建改编':'New reframe','创作者原片预览，非模型改编结果':'Creator source preview, not a generated reframing result','云海栈桥原片':'Original cloud-walk clip','创作者原片':'Creator source','换个画幅，保留原音':'A new frame. The same soundtrack.','需处理':'Needs attention','本机项目':'Local projects','刷新':'Refresh','读取本机项目…':'Loading local projects…','开始新的改编':'Start a new reframe','还没有项目':'No projects yet','导入视频后，项目会保存在这里。':'Your imported videos will appear here.','继续编辑':'Continue editing','已导出':'Exported','待导出':'Ready to export','处理中':'Processing','部分已生成':'In progress','等待生成':'Ready to generate','导入失败':'Import failed','视频项目':'Video project','下载成片':'Download export','项目已刷新':'Projects refreshed','请先粘贴视频链接，或选择一个本地视频。':'Paste a video link or choose a local video.','部分项目无法读取，请检查本机项目文件。':'Some projects could not be read. Check the local project files.'});
const projectsGrid=document.querySelector('#projects-grid'),home=document.querySelector('.home-content');
let projects=[],loadingProjects=false;
function drawProjects(){
 const tr=window.reframeI18n,t=tr.t;
 home.classList.toggle('has-projects',projects.length>0);
 document.querySelector('#projects-count').textContent=projects.length?String(projects.length):'';
 if(!projects.length){const empty=document.createElement('div');empty.className='projects-empty';const label=document.createElement('strong');label.textContent=t('还没有项目');const hint=document.createElement('span');hint.textContent=t('导入视频后，项目会保存在这里。');empty.append(label,hint);projectsGrid.replaceChildren(empty);return}
 projectsGrid.replaceChildren(...projects.map(project=>{
   const card=document.createElement('article');card.className='project-card';
   const link=document.createElement('a');link.className='project-card-main';link.href=`project.html?id=${project.id}`;
   const image=document.createElement('div');image.className='project-card-image';
   if(project.thumbnail){const img=document.createElement('img');img.src=project.thumbnail;img.alt='';img.loading='lazy';image.append(img)}else{image.innerHTML='<svg viewBox="0 0 24 24"><path d="M8 3H4v5m12-5h4v5M4 16v5h4m12-5v5h-4M8 8h8v8H8z"/></svg>'}
   const badge=document.createElement('span');badge.className='project-card-status';badge.dataset.state=project.export_ready?'done':project.busy?'busy':'ready';badge.textContent=t(project.export_ready?'已导出':project.status==='failed'?'导入失败':project.failed_count?'需处理':project.busy||project.status==='importing'?'处理中':project.generated_count===project.segment_count&&project.segment_count?'待导出':project.generated_count?'部分已生成':'等待生成');image.append(badge);
   const title=document.createElement('h3');title.textContent=project.name==='Link import'?t('视频项目'):project.name;title.title=title.textContent;
   const meta=document.createElement('p');const length=project.duration?`${String(Math.floor(project.duration/60)).padStart(2,'0')}:${String(Math.floor(project.duration%60)).padStart(2,'0')}`:'—';meta.textContent=`${length} · ${project.ratio} · ${project.generated_count}/${project.segment_count}`;
   link.append(image,title,meta);
   const bottom=document.createElement('div');bottom.className='project-card-bottom';const time=document.createElement('time');time.dateTime=new Date(project.updated*1000).toISOString();time.textContent=new Intl.DateTimeFormat(tr.language()==='en'?'en-US':'zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit',timeZone:'Asia/Shanghai'}).format(new Date(project.updated*1000));
   const action=document.createElement('a');action.href=project.export_ready?`/media/${project.id}/export.mp4`:`project.html?id=${project.id}`;action.textContent=t(project.export_ready?'下载成片':'继续编辑');if(project.export_ready)action.download='reframed.mp4';bottom.append(time,action);card.append(link,bottom);return card
 }));
}
async function loadProjects(manual=false){
 if(loadingProjects)return;loadingProjects=true;const refresh=document.querySelector('#refresh-projects');refresh.disabled=true;
 try{const response=await fetch('/api/projects',{cache:'no-store',signal:AbortSignal.timeout(15000)});if(!response.ok)throw Error();const data=await response.json();projects=data.projects;drawProjects();if(data.unreadable)window.reframeUI.toast('部分项目无法读取，请检查本机项目文件。','error');if(manual)window.reframeUI.toast('项目已刷新','success')}
 catch{if(!projects.length){const p=document.createElement('p');p.className='projects-placeholder';p.textContent=window.reframeI18n.t('本机项目读取失败，请点击刷新重试。');projectsGrid.replaceChildren(p)}window.reframeUI.toast('本机项目读取失败，请点击刷新重试。','error')}
 finally{loadingProjects=false;refresh.disabled=false}
}
document.querySelector('#refresh-projects').onclick=()=>loadProjects(true);
window.addEventListener('pageshow',()=>{if(importing)resetImport();loadProjects()});
window.addEventListener('pagehide',()=>{importEpoch++});
window.addEventListener('focus',()=>loadProjects());
document.addEventListener('reframe-language',()=>drawProjects());
loadProjects();

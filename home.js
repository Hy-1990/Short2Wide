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


window.reframeI18n.addMessages({
 '开始新的改编':'Start a new reframe','请先粘贴视频链接，或选择一个本地视频。':'Paste a video link or choose a local video.','新建改编':'New reframe','首页':'Home','项目':'Projects','主导航':'Main navigation','Short2Wide 首页':'Short2Wide home','使用说明':'How to use',
 '转换画幅，保留原声。':'A new frame. Your original soundtrack.','查看全部':'View all','全部项目':'All projects','最近项目':'Recent projects',
 '搜索项目名称':'Search projects','项目状态':'Project status','全部状态':'All statuses','未完成':'Unfinished','清除筛选':'Clear filters',
 '正在准备':'Preparing…','尚未分段':'Not segmented yet','没有匹配的项目':'No matching projects','试试其他名称，或清除筛选条件。':'Try another name or clear the filters.',
 '还没有项目':'No projects yet','导入视频后，项目会保存在这里。':'Your imported videos will appear here.','读取本机项目…':'Loading local projects…',
 '继续编辑':'Continue editing','已导出':'Exported','待导出':'Ready to export','处理中':'Processing','部分已生成':'In progress','等待生成':'Ready to generate','导入失败':'Import failed','需处理':'Needs attention',
 '视频项目':'Video project','下载成片':'Download export','刷新':'Refresh','项目已刷新':'Projects refreshed',
 '部分项目无法读取，请检查本机项目文件。':'Some projects could not be read. Check the local project files.',
 '从导入到导出':'From import to export','视频保存在本机，生成通过 DreamAPI 完成。':'Projects stay on your computer. DreamAPI handles generation.',
 '粘贴 YouTube / TikTok 链接，或上传小于5分钟的本地视频，选择目标画幅。':'Paste a YouTube / TikTok link or upload a local video under five minutes, then choose an aspect ratio.',
 '逐段生成与检查':'Generate and review each segment','在右上角配置 DreamAPI 密钥后，生成选中的片段。左右视频可独立播放，“同步播放”会让当前片段从头开始。':'Set your DreamAPI key in the top right, then generate the selected segment. Each video plays independently; Play in sync restarts the current segment on both sides.',
 '确认并导出':'Confirm and export','全部片段生成后，点击一次“确认全部并导出”。成片使用原始音轨。':'Once every segment is generated, click Confirm all & export. The final video uses the original soundtrack.',
 '生成会产生模型费用。画面重建可能改变文字、动作和时序，原音保留不代表同步已保证，请逐段检查。':'Generation incurs model charges. Reconstruction can change text, motion and timing. Keeping the original soundtrack does not guarantee synchronization; review every segment.'
});
const projectsGrid=document.querySelector('#projects-grid');
const search=document.querySelector('#project-search'),statusFilter=document.querySelector('#project-filter');
let projects=[],loadingProjects=false,projectsLoaded=false,projectsError=false,currentView='home';
function element(tag,className,text){const item=document.createElement(tag);if(className)item.className=className;if(text!==undefined)item.textContent=text;return item}
function projectState(project){
 if(project.export_ready)return '已导出';
 if(project.status==='failed')return '导入失败';
 if(project.failed_count)return '需处理';
 if(project.busy||project.status==='importing')return '处理中';
 if(project.generated_count===project.segment_count&&project.segment_count)return '待导出';
 return project.generated_count?'部分已生成':'等待生成';
}
function projectCard(project){
 const tr=window.reframeI18n,t=tr.t;
 const card=element('article','project-card'),link=element('a','project-card-main');link.href=`project.html?id=${project.id}`;
 const image=element('div','project-card-image');image.innerHTML='<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 3H4v5m12-5h4v5M4 16v5h4m12-5v5h-4M8 8h8v8H8z"/></svg>';
 if(project.thumbnail){const img=element('img');img.src=project.thumbnail;img.alt='';img.loading='lazy';img.decoding='async';img.onerror=()=>img.remove();image.append(img)}
 const state=projectState(project),badge=element('span','project-card-status',t(state));
 badge.dataset.state=['导入失败','需处理'].includes(state)?'error':state==='处理中'?'busy':project.export_ready?'done':'ready';image.append(badge);
 const title=element('h3','',project.name==='Link import'?t('视频项目'):project.name);title.title=title.textContent;title.dataset.noTranslate='';
 const meta=element('div','project-card-meta');
 const duration=project.duration?`${String(Math.floor(project.duration/60)).padStart(2,'0')}:${String(Math.floor(project.duration%60)).padStart(2,'0')}`:'—';
 const summary=element('span','',`${duration} · ${project.ratio}`);summary.dataset.noTranslate='';
 const progress=element('span','',project.segment_count?(tr.language()==='en'?`${project.generated_count}/${project.segment_count} generated`:`已生成 ${project.generated_count}/${project.segment_count}`):t(project.status==='importing'||project.busy?'正在准备':'尚未分段'));progress.dataset.noTranslate='';
 meta.append(summary,progress);link.append(image,title,meta);
 const bottom=element('div','project-card-bottom'),date=new Date(project.updated*1000),time=element('time');time.dateTime=date.toISOString();
 time.textContent=new Intl.DateTimeFormat(tr.language()==='en'?'en-US':'zh-CN',{month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'}).format(date);time.dataset.noTranslate='';
 const action=element('a','',t(project.export_ready?'下载成片':'继续编辑'));action.href=project.export_ready?`/media/${project.id}/export.mp4`:`project.html?id=${project.id}`;if(project.export_ready)action.download='reframed.mp4';
 bottom.append(time,action);card.append(link,bottom);return card;
}
function drawProjects(){
 const t=window.reframeI18n.t,all=currentView==='projects';
 document.querySelector('#navigation-project-count').textContent=projectsLoaded?String(projects.length):'';
 let visible=projects;
 if(all){const query=search.value.trim().toLocaleLowerCase();visible=projects.filter(p=>(!query||(p.name==='Link import'?t('视频项目'):p.name).toLocaleLowerCase().includes(query))&&(statusFilter.value==='all'||(statusFilter.value==='exported'?p.export_ready:!p.export_ready)))}else visible=projects.slice(0,6);
 document.querySelector('#projects-count').textContent=projectsLoaded?(all&&visible.length!==projects.length?`${visible.length} / ${projects.length}`:String(visible.length)):'';
 if(!projectsLoaded){const p=element('p','projects-placeholder',t(projectsError?'本机项目读取失败，请点击刷新重试。':'读取本机项目…'));projectsGrid.replaceChildren(p);document.querySelector('#refresh-projects').hidden=!projectsError&&!all;return}
 if(!visible.length){
  const empty=element('div','projects-empty');empty.append(element('strong','',t(projects.length?'没有匹配的项目':'还没有项目')),element('p','',t(projects.length?'试试其他名称，或清除筛选条件。':'导入视频后，项目会保存在这里。')));
  if(projects.length){const clear=element('button','text-button',t('清除筛选'));clear.type='button';clear.onclick=()=>{search.value='';statusFilter.value='all';drawProjects();search.focus()};empty.append(clear)}else if(all){const create=element('a','',t('新建改编'));create.href='#new';empty.append(create)}
  projectsGrid.replaceChildren(empty);return;
 }
 projectsGrid.replaceChildren(...visible.map(projectCard));
}
function focusImport(){source.focus();source.scrollIntoView({block:'center'})}
function route(){
 const hash=location.hash.slice(1);currentView=['projects','help'].includes(hash)?hash:'home';const t=window.reframeI18n.t;
 document.querySelector('#page-title').textContent=t(currentView==='projects'?'项目':currentView==='help'?'使用说明':'首页');
 document.querySelector('#new-project').hidden=currentView!=='home';
 document.querySelector('#project-library').hidden=currentView==='help';
 document.querySelector('#usage-guide').hidden=currentView!=='help';
 document.querySelector('#project-filters').hidden=currentView!=='projects';
 document.querySelector('#projects-title').textContent=t(currentView==='projects'?'全部项目':'最近项目');
 document.querySelector('#all-projects-link').hidden=currentView!=='home';
 document.querySelector('#refresh-projects').hidden=currentView!=='projects'&&!projectsError;
 document.querySelectorAll('[data-navigation]').forEach(link=>{if(link.dataset.navigation===currentView)link.setAttribute('aria-current','page');else link.removeAttribute('aria-current')});
 drawProjects();if(hash==='new')focusImport();
}
async function loadProjects(manual=false){
 if(loadingProjects)return;loadingProjects=true;const refresh=document.querySelector('#refresh-projects');refresh.disabled=true;
 try{const response=await fetch('/api/projects',{cache:'no-store',signal:AbortSignal.timeout(15000)});if(!response.ok)throw Error();const data=await response.json();projects=data.projects;projectsLoaded=true;projectsError=false;drawProjects();refresh.hidden=currentView!=='projects';if(data.unreadable)window.reframeUI.toast('部分项目无法读取，请检查本机项目文件。','error');if(manual)window.reframeUI.toast('项目已刷新','success')}
 catch{projectsError=true;drawProjects();refresh.hidden=false;window.reframeUI.toast('本机项目读取失败，请点击刷新重试。','error')}
 finally{loadingProjects=false;refresh.disabled=false}
}
document.querySelector('#refresh-projects').onclick=()=>loadProjects(true);
search.addEventListener('input',drawProjects);statusFilter.addEventListener('change',drawProjects);
document.querySelector('.sidebar-create').addEventListener('click',()=>{if(location.hash==='#new')focusImport()});
window.addEventListener('hashchange',()=>{window.scrollTo(0,0);route()});
window.addEventListener('pageshow',()=>{if(importing)resetImport();route();loadProjects()});
window.addEventListener('pagehide',()=>{importEpoch++});
window.addEventListener('focus',()=>loadProjects());
document.addEventListener('reframe-language',()=>route());
route();loadProjects();

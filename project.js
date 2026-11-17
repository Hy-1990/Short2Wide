(()=>{
const $=s=>document.querySelector(s),tr=window.reframeI18n;
tr.addMessages({
'读取项目…':'Loading project…','准备视频':'Preparing video','正在读取素材…':'Reading media…','同步播放':'Play in sync','暂停':'Pause','合成导出':'Build export','下载视频':'Download video','预览声音':'Preview audio','原音 + 对齐画面':'Original audio + aligned video','模型原生音画':'Model video & audio','先生成这个片段':'Generate this segment first','默认将画面时长归一到原片。文字、动作与口型需要逐段核对。':'Video duration is fitted to the original. Review text, motion and lip sync segment by segment.','视频片段':'Segments','补充需要保留或调整的内容':'What should be preserved or adjusted?','参考片段会上传到 DreamAPI，点击生成会产生模型费用。真人参考素材可能被接口拒绝。':'Reference clips are uploaded to DreamAPI. Generation incurs model charges. Real-person references may be rejected.','生成这个片段':'Generate segment','对齐两个节点':'Align two cues','找出原片与模型原生画面中相同的两个事件，填写各自的片段内秒数。':'Find two matching events in the original and native generated video. Enter their local times in seconds.','节点':'Cue','原片 / 秒':'Original / s','生成 / 秒':'Generated / s','应用节点对齐':'Apply alignment','重置':'Reset','两点校正偏移和速度，不保证中间所有事件同步。':'Two cues adjust offset and speed; intervening events still need review.','已检查文字、动效和声音对应关系':'I checked text, motion and audio alignment','等待生成':'Ready','上传参考素材…':'Uploading reference…','模型生成中…':'Generating…','对齐画面…':'Aligning…','待核对':'Review','生成失败':'Failed','继续查询同一任务':'Resume same task','提交状态不明':'Submission uncertain','已核对':'Approved','重新生成':'Regenerate','本次重新生成会上传参考片段并创建新的计费任务，继续吗？':'Regeneration uploads the reference and creates a new billable task. Continue?','请求失败，请重试。':'Request failed. Please retry.','项目不存在，请返回首页导入视频。':'Project not found. Import a video from the homepage.','原片无音轨':'The original has no audio track','首版使用画面变化与停顿切分，暂不做语义识别。':'Segments follow scene changes and pauses, without semantic recognition.','节点1原片秒数':'Cue 1 original seconds','节点1生成秒数':'Cue 1 generated seconds','节点2原片秒数':'Cue 2 original seconds','节点2生成秒数':'Cue 2 generated seconds','请先在右上角配置 DreamAPI 密钥。':'Configure your DreamAPI key in the top right first.','完整原音轨会用于最终导出。':'Final export uses the full original audio.','模型原生音画仅用于检查，不会用于最终音轨。':'Native model audio is for review only; it is not used in the final soundtrack.','请等待当前处理完成。':'Wait for the current operation to finish.','操作失败':'Operation failed','视频必须小于5分钟，请先截取后再导入。':'Video must be under five minutes. Trim it before importing.','读取画面与音频…':'Reading video and audio…','按画面变化和停顿分段…':'Splitting on scene changes and pauses…','下载视频…':'Downloading video…','导入视频…':'Importing video…','可以先生成一个片段。':'Start by generating one segment.','合成画面并保留完整原音轨…':'Assembling video with the original soundtrack…','已导出，音频取自原始素材。':'Export ready. Audio comes from the original media.','暂停同步播放':'Pause synced playback','提交结果不明，请先在 DreamAPI 控制台核实任务，避免重复计费。':'Submission is uncertain. Check the task in DreamAPI before retrying to avoid duplicate charges.','请填写两组有效时间点。':'Enter two valid cue pairs.','合成测试素材 · 非模型生成':'Synthetic test media · Not model generated','时间点须递增，并在各自片段时长以内。':'Cue times must increase and stay within each clip.','请提供两组对应时间点。':'Provide two matching cue pairs.','这两组节点需要过大的变速，请重新选择或重新生成片段。':'These cues require an extreme speed change. Choose different cues or regenerate.','请等待片段处理完成后再确认。':'Wait for processing before approving.','请先生成并确认所有片段。':'Generate and approve every segment first.','导入已中断，请返回首页重新导入。':'Import was interrupted. Return home and import again.'
});
tr.addMessages({'确认全部并导出':'Confirm all & export','正在合成…':'Building export…','所有片段已生成，可以一次确认并导出。':'All segments are ready. Confirm all and export in one click.','高级选项':'Advanced options','错误详情':'Error details','播放':'Play','单独播放原片':'Play original independently','单独播放生成视频':'Play generated video independently','暂停原片':'Pause original','暂停生成视频':'Pause generated video','已生成':'Generated','正在上传参考素材':'Uploading reference media','正在生成新的画幅':'Generating the new frame','正在对齐画面':'Aligning the video','上传完成后会自动开始生成。':'Generation starts automatically after the upload.','生成通常需要3–10分钟，可离开后从首页继续。':'Usually 3–10 minutes. You can return from Local projects later.','正在处理本机画面，原音保持不变。':'Processing the video locally. The original audio stays unchanged.','已提交生成任务':'Generation started','正在继续查询原任务':'Resuming the existing task','已开始合成导出':'Export started','视频已导出，可以下载了':'Your video is ready to download','节点对齐已完成':'Cue alignment applied','已恢复默认对齐':'Default alignment restored','视频播放失败，请重新打开项目后重试。':'Video playback failed. Reopen the project and retry.','生成已完成':'Generation finished','片段处理失败':'Segment processing failed','同步播放失败，请重试。':'Could not start synced playback. Please retry.','原片音轨':'Original soundtrack','本机交互测试副本':'Local interaction test copy','生成模型音频，仅用于对照':'Generate model audio for comparison','关闭后，生成画面仍会使用原片音轨预览与导出。':'When off, previews and exports still use the original soundtrack.','模型原生画面（无音轨）':'Native model video (silent)'});
const id=new URLSearchParams(location.search).get('id');
let project,active=0,signature='',busy=false,refreshTimer,previewKey='',drafts={},audioDrafts={},localError='',lastNotifiedError='',reconnecting=false,epoch=0,pendingAction='',seen=false,lastExport=false;
let syncing=false,startingSync=false,syncEpoch=0,soloMutes=[false,false];
const states=new Map(),controlledSeeks=new WeakMap(),source=$('#source-video'),result=$('#result-video'),ui=window.reframeUI;
const statuses={ready:'等待生成',uploading:'上传参考素材…',generating:'模型生成中…',processing:'对齐画面…',review:'已生成',failed:'生成失败',resumable:'继续查询同一任务',interrupted:'提交状态不明'};
const t=s=>tr.t(s),media=name=>`/media/${id}/${name}`,fmt=s=>`${String(Math.floor(s/60)).padStart(2,'0')}:${String(Math.floor(s%60)).padStart(2,'0')}`;
const segmentLabel=i=>tr.language()==='en'?`Segment ${String(i+1).padStart(2,'0')}`:`片段 ${String(i+1).padStart(2,'0')}`;
async function api(path,body){
 const response=await fetch(path,{...(body===undefined?{cache:'no-store'}:{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}),signal:AbortSignal.timeout(20000)});
 let data;try{data=await response.json()}catch{throw Error('请求失败，请重试。')}
 if(!response.ok)throw Error(data.error||'请求失败，请重试。');return data;
}
function showError(error){
 const raw=String(error?.message||error);localError=raw;
 $('#project-error').hidden=false;$('#project-error-summary').textContent=ui.message(raw);$('#project-error-detail').textContent=raw;
 if(raw!==lastNotifiedError){ui.toast(ui.message(raw),'error');lastNotifiedError=raw}
}
function currentShot(){return project?.shots[active]}
function setSource(video,url){if(video.getAttribute('src')!==url)video.src=url}
function seek(video,time){controlledSeeks.set(video,time);video.currentTime=time}
function playerLabels(){
 $('#play-source').textContent=t(source.paused?'播放':'暂停');$('#play-result').textContent=t(result.paused?'播放':'暂停');
 $('#play-source').setAttribute('aria-label',t(source.paused?'单独播放原片':'暂停原片'));$('#play-result').setAttribute('aria-label',t(result.paused?'单独播放生成视频':'暂停生成视频'));
 $('#sync-play').textContent=t(syncing?'暂停同步播放':'同步播放');
}
function leaveSync(pauseBoth=false){
 syncEpoch++;const restore=syncing||startingSync;syncing=false;startingSync=false;
 if(pauseBoth){source.pause();result.pause()}
 source.playbackRate=1;result.playbackRate=1;
 if(restore){source.muted=soloMutes[0];result.muted=soloMutes[1]}
 playerLabels();
}
function resetPreview(){
 const s=currentShot();if(!s)return;leaveSync(true);
 $('#audio-mode').querySelector('[value=native]').disabled=!s.generated_duration;$('#audio-mode').querySelector('[value=native]').textContent=t(s.generated_duration&&!s.generated_audio?'模型原生画面（无音轨）':'模型原生音画');
 if(!s.generated_duration)$('#audio-mode').value='original';
 const native=$('#audio-mode').value==='native';
 source.muted=false;result.muted=false;setSource(source,media('source.mp4'));seek(source,s.start);
 const has=s.generated_duration&&['review','resumable','processing'].includes(s.status);
 result.hidden=!has;$('#output-empty').hidden=!!has||project.busy&&['uploading','generating','processing'].includes(s.status);
 if(has){setSource(result,media(`shot-${active}-${native?'generated':'preview'}.mp4?v=${s.version||s.scale||1}-${s.offset||0}`));result.controls=true;seek(result,0)}
 $('#preview-note').textContent=project.test_fixture?t('本机交互测试副本'):t(native?'模型原生音画仅用于检查，不会用于最终音轨。':project.audio?'默认将画面时长归一到原片。文字、动作与口型需要逐段核对。':'原片无音轨');playerLabels();
}
function observeChanges(next){
 if(seen){
  for(const shot of next.shots){const previous=states.get(shot.index);if(!previous)continue;
   if(shot.status==='review'&&previous!=='review')ui.toast(project.operation==='align'?pendingAction==='reset'?'已恢复默认对齐':'节点对齐已完成':`${segmentLabel(shot.index)} · ${t('生成已完成')}`,'success');
   if(['failed','resumable','interrupted'].includes(shot.status)&&previous!==shot.status)ui.toast(`${segmentLabel(shot.index)} · ${ui.message(shot.error||'片段处理失败')}`,'error');
  }
  if(next.export_ready&&!lastExport)ui.toast('视频已导出，可以下载了','success');
 }
 next.shots.forEach(s=>states.set(s.index,s.status));lastExport=next.export_ready;seen=true;
}
function clock(){if(project&&project.status==='importing'){const elapsed=Math.max(0,Math.floor(Date.now()/1000-(project.operation_started||project.created)));$('#loading-clock').textContent=tr.language()==='en'?`Elapsed ${fmt(elapsed)}`:`已用时 ${fmt(elapsed)}`;return}const s=currentShot();if(!s)return;const working=project.busy&&['uploading','generating','processing'].includes(s.status);if(!working)return;const elapsed=Math.max(0,Math.floor(Date.now()/1000-(project.operation_started||Date.now()/1000)));$('#render-clock').textContent=tr.language()==='en'?`Elapsed ${fmt(elapsed)}`:`已用时 ${fmt(elapsed)}`}
function draw(force=false){
 $('#project-name').textContent=project.name;
 const ready=project.status==='ready';$('#loading').hidden=ready;$('#project-editor').hidden=!ready;
 if(!ready){$('#loading').classList.toggle('is-failed',project.status==='failed');$('#loading-message').textContent=project.error?ui.message(project.error):t(project.message);if(project.error&&project.error!==lastNotifiedError)showError(project.error);return}
 const s=currentShot();if(!s)return;
 $('#segment-title').textContent=segmentLabel(active);$('#segment-info').textContent=`${fmt(s.start)} — ${fmt(s.end)} · ${s.duration.toFixed(2)}s`;$('#project-ratio').textContent=project.ratio;
 const count=project.shots.filter(x=>x.status==='review').length,allReady=count===project.shots.length&&count>0;
 $('#project-progress').textContent=tr.language()==='en'?`${count} / ${project.shots.length} generated`:`已生成 ${count} / ${project.shots.length} 段`;
 const nextSignature=JSON.stringify(project.shots.map(x=>x.status))+'-'+active+'-'+tr.language();
 if(force||signature!==nextSignature){signature=nextSignature;$('#real-shots').replaceChildren(...project.shots.map((shot,index)=>{
  const button=document.createElement('button');button.className=`real-shot ${index===active?'selected':''}`;button.type='button';button.setAttribute('aria-label',segmentLabel(index));button.setAttribute('aria-pressed',String(index===active));
  const img=document.createElement('img');img.src=media(`shot-${index}.jpg`);img.alt='';const n=document.createElement('span');n.textContent=String(index+1).padStart(2,'0');const time=document.createElement('small');time.textContent=`${fmt(shot.start)} — ${fmt(shot.end)}`;const state=document.createElement('em');if(['uploading','generating','processing'].includes(shot.status)&&project.busy){const dot=document.createElement('i');dot.className='working-dot';dot.setAttribute('aria-hidden','true');state.append(dot)}state.append(document.createTextNode(t(statuses[shot.status]||shot.status)));button.append(img,n,time,state);button.onclick=()=>{drafts[active]=$('#real-prompt').value;active=index;previewKey='';localError='';lastNotifiedError='';draw(true)};return button
 }))}
 $('#output-message').textContent=t(statuses[s.status]||'先生成这个片段');
 $('#model-status').textContent=s.status==='interrupted'?t('提交结果不明，请先在 DreamAPI 控制台核实任务，避免重复计费。'):s.error?ui.message(s.error):t(statuses[s.status]||s.status);
 const working=project.busy&&['uploading','generating','processing'].includes(s.status);$('#render-progress').hidden=!working;$('.output-stage').setAttribute('aria-busy',String(working));
 $('#render-title').textContent=t(s.status==='uploading'?'正在上传参考素材':s.status==='generating'?'正在生成新的画幅':'正在对齐画面');$('#render-hint').textContent=t(s.status==='uploading'?'上传完成后会自动开始生成。':s.status==='generating'?'生成通常需要3–10分钟，可离开后从首页继续。':'正在处理本机画面，原音保持不变。');clock();
 const exporting=project.busy&&project.operation==='export';
 $('#project-status').textContent=exporting?t('合成画面并保留完整原音轨…'):working?t(statuses[s.status]):t('首版使用画面变化与停顿切分，暂不做语义识别。');
 if(project.error)showError(project.error);else if(s.error&&['failed','resumable','interrupted'].includes(s.status))showError(s.error);else if(!localError)$('#project-error').hidden=true;
 $('#generate-segment').disabled=project.busy||busy||s.status==='interrupted';$('#generate-segment').classList.toggle('is-working',working);$('#generate-segment').textContent=t(working?statuses[s.status]:s.status==='resumable'?'继续查询同一任务':s.status==='review'||s.status==='failed'?'重新生成':'生成这个片段');
 $('#export-project').disabled=project.busy||busy||!allReady;$('#export-project').classList.toggle('is-working',exporting||pendingAction==='export'&&busy);$('#export-project').textContent=t(exporting?'正在合成…':'确认全部并导出');
 $('#export-hint').textContent=project.export_ready?'':exporting?t('合成画面并保留完整原音轨…'):allReady?t('所有片段已生成，可以一次确认并导出。'):tr.language()==='en'?`${project.shots.length-count} ${project.shots.length-count===1?'segment':'segments'} still ${project.shots.length-count===1?'needs':'need'} generation`:`还有 ${project.shots.length-count} 个片段未生成`;
 $('#export-project').hidden=project.export_ready;$('#download-export').hidden=!project.export_ready;$('#download-export').href=media('export.mp4');$('#download-export').download='reframed.mp4';
 $('#align-section').hidden=false;$('#cue-options').hidden=s.status!=='review';$('#model-audio').disabled=project.busy||busy||s.status==='resumable';$('#apply-alignment').disabled=project.busy||busy;$('#reset-alignment').disabled=project.busy||busy;$('#real-prompt').disabled=project.busy||s.status==='resumable';$('#play-result').disabled=!s.generated_duration||working;$('#sync-play').disabled=!s.generated_duration||working;
 const key=`${active}-${s.status}-${s.scale}-${s.offset}-${s.task_id}-${s.version}`;
 if(previewKey!==key){previewKey=key;$('#real-prompt').value=drafts[active]??s.prompt;$('#model-audio').checked=audioDrafts[active]??s.generate_audio??true;const a=s.anchors.length?s.anchors:[[0,0],[s.duration,s.generated_duration||s.duration]];['s1','g1','s2','g2'].forEach((x,i)=>$('#anchor-'+x).value=Number(a[Math.floor(i/2)][i%2]).toFixed(2));resetPreview()}
}
async function refresh(){
 const ticket=epoch;try{if(busy)return;const next=await api(`/api/projects/${id}`);if(ticket!==epoch)return;project=next;if(reconnecting){localError='';lastNotifiedError='';reconnecting=false}observeChanges(next);draw()}
 catch(error){reconnecting=true;$('#loading-message').textContent=ui.message(error);showError(error)}finally{refreshTimer=setTimeout(refresh,2000)}
}
async function action(name,body={},intent=name){
 if(busy)return;busy=true;epoch++;pendingAction=intent;localError='';lastNotifiedError='';project.error='';$('#project-error').hidden=true;draw();
 try{await api(`/api/projects/${id}/${name}`,body);project=await api(`/api/projects/${id}`);observeChanges(project);draw();if(name==='generate')ui.toast(body.retry?'已提交生成任务':states.get(active)==='resumable'?'正在继续查询原任务':'已提交生成任务','info');if(name==='export')ui.toast('已开始合成导出','info')}
 catch(error){showError(error)}finally{busy=false;draw()}
}
$('#generate-segment').onclick=()=>{if(!project.configured){document.querySelector('.control-key').click();showError(t('请先在右上角配置 DreamAPI 密钥。'));return}const s=currentShot(),retry=['review','failed'].includes(s.status);if(retry&&!confirm(t('本次重新生成会上传参考片段并创建新的计费任务，继续吗？')))return;drafts[active]=$('#real-prompt').value;action('generate',{index:active,prompt:drafts[active],retry,generate_audio:$('#model-audio').checked})};
$('#model-audio').onchange=()=>{audioDrafts[active]=$('#model-audio').checked};
$('#real-prompt').oninput=()=>{drafts[active]=$('#real-prompt').value};
$('#apply-alignment').onclick=()=>{const values=['s1','g1','s2','g2'].map(x=>$('#anchor-'+x).value);if(values.some(x=>x==='')){showError('请填写两组有效时间点。');return}action('align',{index:active,anchors:[[+values[0],+values[1]],[+values[2],+values[3]]]})};
$('#reset-alignment').onclick=()=>action('align',{index:active,anchors:[]},'reset');$('#export-project').onclick=()=>action('export',{confirm_all:true});$('#audio-mode').onchange=resetPreview;
async function seekReady(video,time){
 if(video.readyState<1)await new Promise((resolve,reject)=>{let timer;const clear=()=>{clearTimeout(timer);video.removeEventListener('loadedmetadata',done);video.removeEventListener('error',fail)};const done=()=>{clear();resolve()};const fail=()=>{clear();reject(Error('视频播放失败，请重新打开项目后重试。'))};video.addEventListener('loadedmetadata',done);video.addEventListener('error',fail);timer=setTimeout(fail,12000)});
 if(Math.abs(video.currentTime-time)<.02)return;
 await new Promise((resolve,reject)=>{let timer;const clear=()=>{clearTimeout(timer);video.removeEventListener('seeked',done);video.removeEventListener('error',fail)};const done=()=>{clear();resolve()};const fail=()=>{clear();reject(Error('同步播放失败，请重试。'))};video.addEventListener('seeked',done);video.addEventListener('error',fail);timer=setTimeout(fail,12000);seek(video,time)});
}
async function syncPlay(){
 if(syncing){leaveSync(true);return}const s=currentShot();if(!s||result.hidden)return;
 leaveSync(true);const ticket=++syncEpoch;startingSync=true;$('#sync-play').disabled=true;
 try{await Promise.all([seekReady(source,s.start),seekReady(result,0)]);if(ticket!==syncEpoch)return;soloMutes=[source.muted,result.muted];const native=$('#audio-mode').value==='native';source.muted=native&&!!s.generated_audio;result.muted=!(native&&s.generated_audio);result.playbackRate=native?s.generated_duration/s.duration:1;syncing=true;await Promise.all([source.play(),result.play()]);if(ticket!==syncEpoch)return;startingSync=false;playerLabels()}
 catch(error){leaveSync(true);showError(error)}finally{$('#sync-play').disabled=false}
}
$('#sync-play').onclick=syncPlay;
async function toggleSolo(video){leaveSync(false);try{if(video.paused){const s=currentShot();if(video===source&&(source.currentTime<s.start||source.currentTime>=s.end))await seekReady(source,s.start);await video.play()}else video.pause();playerLabels()}catch(error){showError(error)}}
$('#play-source').onclick=()=>toggleSolo(source);$('#play-result').onclick=()=>toggleSolo(result);
for(const video of [source,result]){
 video.addEventListener('play',()=>{playerLabels()});
 video.addEventListener('pause',()=>{if(syncing&&!startingSync)leaveSync(false);playerLabels()});
 video.addEventListener('seeking',()=>{const target=controlledSeeks.get(video);if(target!==undefined&&Math.abs(video.currentTime-target)<.2){controlledSeeks.delete(video);return}if(syncing&&!startingSync)leaveSync(false)});
 video.addEventListener('ended',()=>{if(syncing)leaveSync(true);playerLabels()});
 video.addEventListener('error',()=>{if(!video.hidden&&video.getAttribute('src'))showError('视频播放失败，请重新打开项目后重试。')});
}
source.addEventListener('timeupdate',()=>{const s=currentShot();if(!s)return;$('#source-clock').textContent=Math.min(s.duration,Math.max(0,source.currentTime-s.start)).toFixed(2)+'s';if(!source.paused&&source.currentTime>=s.end){if(syncing)leaveSync(true);else source.pause()}if(syncing&&!startingSync&&!source.paused){const rate=$('#audio-mode').value==='native'?s.generated_duration/s.duration:1,target=(source.currentTime-s.start)*rate;if(Math.abs(result.currentTime-target)>.25)seek(result,Math.max(0,target))}});
const progressTimer=setInterval(clock,1000);
document.addEventListener('reframe-language',()=>{signature='';if(project)draw(true);playerLabels()});
window.addEventListener('pagehide',()=>{clearTimeout(refreshTimer);clearInterval(progressTimer);leaveSync(true)});
if(!/^[0-9a-f]{32}$/.test(id||''))$('#loading-message').textContent=t('项目不存在，请返回首页导入视频。');else refresh();
})();

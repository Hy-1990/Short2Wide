(()=>{
 const tr=window.reframeI18n;
 tr.addMessages({
 '服务商拒绝了生成音频，可关闭模型音频后手动重试。':'The provider rejected the generated audio. Disable model audio before manually retrying.','关闭通知':'Dismiss notification','操作完成':'Done','操作失败，请查看错误详情后重试。':'The operation failed. Check the error details and retry.','无法连接本机服务，请确认服务已启动后重试。':'Cannot reach the local server. Check that it is running and retry.','连接超时，请继续查询原任务。':'Connection timed out. Resume the existing task.','密钥验证失败，请检查 DreamAPI 设置。':'Authentication failed. Check your DreamAPI key.','余额不足，请充值后重试。':'Insufficient balance. Add credits and retry.','请求过于频繁，请稍后重试。':'Too many requests. Please retry shortly.','服务商拒绝了参考素材，请查看错误详情。':'The provider rejected the reference media. Check the error details.','本机项目读取失败，请点击刷新重试。':'Could not load local projects. Select Refresh to retry.','请先生成全部片段。':'Generate every segment before exporting.','请点击确认全部并导出。':'Select Confirm all & export.','这个项目仍在处理，请等待当前步骤完成。':'This project is processing. Wait for the current step to finish.','当前项目仍在处理中。':'This project is still processing.','请选择有效片段。':'Select a valid segment.','请填写两组有效时间点。':'Enter two valid cue pairs.','请先生成这个片段。':'Generate this segment first.','本机处理失败，请重试。':'Local processing failed. Please retry.','请使用小于512MB的视频文件。':'Use a video file under 512 MB.','视频必须小于5分钟，请先截取后再导入。':'Video must be under five minutes. Trim it before importing.','时间点须递增，并在各自片段时长以内。':'Cue times must increase and stay within each clip.','无法读取视频时长。':'Could not read the video duration.','文件中没有可读取的视频画面。':'No readable video stream was found.','请使用有效的 YouTube 或 TikTok 视频链接。':'Use a valid YouTube or TikTok video link.','上传中断，请重新选择文件。':'Upload interrupted. Select the file again.','下载未完成；视频可能受登录限制或不小于5分钟。可以改用本地文件。':'Download failed. The video may require login or be too long. Try a local file.','导入已中断，请返回首页重新导入。':'Import was interrupted. Return home and import again.','找不到本机 DreamAPI skill，请先安装。':'The local DreamAPI skill is missing. Install it before generating.','画面要求请控制在1000字以内。':'Keep the visual direction under 1,000 characters.'
 });
 const lang=()=>tr.language();
 function message(error){
  const raw=String(error?.message||error||'操作失败，请查看错误详情后重试。');
  const translated=tr.t(raw);
  if(translated!==raw)return translated;
  const common=/audio.*sensitive|音频.*敏感|敏感.*音频/i.test(raw)?'服务商拒绝了生成音频，可关闭模型音频后手动重试。':/failed to fetch|networkerror|network request|load failed|econnrefused/i.test(raw)?'无法连接本机服务，请确认服务已启动后重试。':/timeout|timed out/i.test(raw)?'连接超时，请继续查询原任务。':/401|unauthorized|invalid.?api.?key|invalid token/i.test(raw)?'密钥验证失败，请检查 DreamAPI 设置。':/insufficient|balance|credits|余额不足/i.test(raw)?'余额不足，请充值后重试。':/429|too many requests|rate limit/i.test(raw)?'请求过于频繁，请稍后重试。':/real.person|real.human|face|reference.*reject|真人|人脸/i.test(raw)?'服务商拒绝了参考素材，请查看错误详情。':null;
  if(common)return tr.t(common);
  if(lang()==='zh'&&/[\u3400-\u9fff]/.test(raw)&&raw.length<200)return raw;
  if(lang()==='en'&&!/[\u3400-\u9fff]/.test(raw)&&raw.length<200)return raw;
  return tr.t('操作失败，请查看错误详情后重试。');
 }
 const stack=document.createElement('div');stack.className='notification-stack';document.body.append(stack);
 function toast(text,type='info'){
  const host=document.querySelector('dialog[open]')||document.body;if(stack.parentElement!==host)host.append(stack);
  const item=document.createElement('div');item.className='notification';item.dataset.type=type;item.setAttribute('role',type==='error'?'alert':'status');
  const mark=document.createElementNS('http://www.w3.org/2000/svg','svg');mark.setAttribute('viewBox','0 0 24 24');mark.innerHTML=type==='success'?'<path d="m5 12 4 4L19 6"/>':type==='error'?'<circle cx="12" cy="12" r="8"/><path d="M12 7v6m0 3v1"/>':'<circle cx="12" cy="12" r="8"/><path d="M12 11v5m0-9v1"/>';
  const copy=document.createElement('span');copy.textContent=type==='error'?message(text):tr.t(text);
  const close=document.createElement('button');close.type='button';close.setAttribute('aria-label',tr.t('关闭通知'));close.innerHTML='<svg viewBox="0 0 24 24"><path d="m7 7 10 10M17 7 7 17"/></svg>';close.onclick=()=>item.remove();
  item.append(mark,copy,close);stack.append(item);while(stack.children.length>3)stack.firstElementChild.remove();setTimeout(()=>item.remove(),type==='error'?8500:4500);
 }
 document.addEventListener('close',()=>{if(!document.querySelector('dialog[open]'))document.body.append(stack)},true);
 window.reframeUI={toast,message};
})();

"use strict";
(() => {
 const sidebar=document.getElementById("report-sidebar");
 const menu=document.getElementById("open-navigation");
 const close=document.getElementById("close-navigation");
 const search=document.getElementById("chapter-search");
 const filter=document.getElementById("subject-filter");
 const results=document.getElementById("chapter-results");
 const status=document.getElementById("search-status");
 const main=document.getElementById("main-content");
 const locationLabel=document.getElementById("reading-location");
 const groups=new Map();
 function groupFor(node){
  if(node.closest("#topper-insights"))return "Preparation / topper tips & traps";
  if(node.closest("#chapters-ESI"))return "ESI / chapter targets";
  if(node.closest("#chapters-Finance"))return "FM / finance chapters";
  if(node.closest("#chapters-Management"))return "FM / management chapters";
  if(node.closest("#chapters-English"))return "English / chapter targets";
  if(node.closest("#what-ESI"))return "ESI / reports, schemes & policies";
  if(node.closest("#what-FM"))return "FM / named topics & policies";
  if(node.closest("#what-English"))return "English / essay, precis & RC";
  if(node.closest("#ESI"))return "ESI / original deep analysis";
  if(node.closest("#FM"))return "FM / original deep analysis";
  if(node.closest("#English"))return "English / original deep analysis";
  return "Overview / distribution & evidence";
 }
 const nodes=[...main.querySelectorAll(".inventory-card,.study-task,main > article")];
 for(const article of main.querySelectorAll("article")){
  if(!article.querySelector(".inventory-card"))nodes.push(article);
 }
 const entries=[...new Set(nodes)].map((node,i)=>{
  const heading=node.querySelector("h2,h3,h4,h5");
  if(!node.id)node.id=`reading-item-${i+1}`;
  const title=heading?.textContent.trim()||"Study section";
  const group=groupFor(node);
  const searchable=node.cloneNode(true);
  searchable.querySelectorAll(".ai-prompt").forEach(prompt=>prompt.remove());
  return {node,title,group,text:searchable.textContent.toLocaleLowerCase()};
 });
 for(const entry of entries){
  if(!groups.has(entry.group)){
   const detail=document.createElement("details");
   detail.className="toc-group";
   const summary=document.createElement("summary");
   summary.textContent=entry.group;
   const list=document.createElement("ul");
   detail.append(summary,list);results.append(detail);
   groups.set(entry.group,{detail,list,items:[]});
  }
  const group=groups.get(entry.group);
  const item=document.createElement("li");
  const link=document.createElement("a");
  link.href=`#${entry.node.id}`;link.textContent=entry.title;
  item.append(link);group.list.append(item);group.items.push({...entry,item,link});
 }
 function renderSearch(){
  const words=search.value.trim().toLocaleLowerCase().split(/\s+/).filter(Boolean);
  const subject=filter.value;
  let count=0;
  for(const [name,group]of groups){
   let visible=0;
   for(const entry of group.items){
    const matches=(!subject||name.startsWith(subject))&&words.every(word=>entry.text.includes(word));
    entry.item.hidden=!matches;
    if(matches)visible++;
   }
   group.detail.hidden=visible===0;
   if(words.length||subject)group.detail.open=visible>0;
   count+=visible;
  }
  status.textContent=count?`${count} study sections. Search includes the text inside each section.`:"No matches. Try a shorter term or choose all subjects.";
 }
 search.addEventListener("input",renderSearch);
 filter.addEventListener("change",renderSearch);
 document.getElementById("clear-search").addEventListener("click",()=>{
  search.value="";filter.value="";renderSearch();search.focus();
 });
 function setDrawer(open,restoreFocus=true){
  sidebar.classList.toggle("is-open",open);menu.setAttribute("aria-expanded",String(open));
  if(open)close.focus();
  else if(restoreFocus)menu.focus();
 }
 menu.addEventListener("click",()=>setDrawer(!sidebar.classList.contains("is-open")));
 close.addEventListener("click",()=>setDrawer(false));
 sidebar.addEventListener("keydown",event=>{
  if(!sidebar.classList.contains("is-open"))return;
  if(event.key==="Escape"){event.preventDefault();setDrawer(false);}
  if(event.key==="Tab"){
   const focusable=[...sidebar.querySelectorAll("button,input,select,a,summary")].filter(el=>el.getClientRects().length&&!el.disabled);
   const first=focusable[0],last=focusable.at(-1);
   if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}
   else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}
  }
 });
 function syncAnchor(focus=false){
  const id=decodeURIComponent(location.hash.slice(1));
  const target=document.getElementById(id);
  document.querySelectorAll(".sidebar a[aria-current]").forEach(a=>a.removeAttribute("aria-current"));
  if(!target){locationLabel.textContent="Choose a chapter or search the complete report.";return;}
  const heading=target.matches("h1,h2,h3,h4,h5")?target:target.querySelector("h1,h2,h3,h4,h5");
  locationLabel.textContent=`Reading: ${heading?.textContent||"Report overview"}`;
  for(const a of sidebar.querySelectorAll("a")){
   if(a.hash===location.hash){
    a.setAttribute("aria-current","location");
    const detail=a.closest("details");if(detail)detail.open=true;
   }
  }
  if(focus){target.setAttribute("tabindex","-1");target.focus({preventScroll:true});}
 }
 sidebar.addEventListener("click",event=>{
  if(event.target.closest("a")){
   setDrawer(false,false);
   setTimeout(()=>syncAnchor(true),0);
  }
 });
 window.addEventListener("hashchange",()=>syncAnchor(true));
 let fontSize=17;
 function resizeText(delta){
  fontSize=Math.max(15,Math.min(23,fontSize+delta));
  document.documentElement.style.setProperty("--reading-size",`${fontSize}px`);
  document.getElementById("text-size-status").textContent=`Reading text ${fontSize} pixels`;
  document.getElementById("smaller-text").disabled=fontSize===15;
  document.getElementById("larger-text").disabled=fontSize===23;
 }
 document.getElementById("smaller-text").addEventListener("click",()=>resizeText(-1));
 document.getElementById("larger-text").addEventListener("click",()=>resizeText(1));
 document.getElementById("focus-reading").addEventListener("click",event=>{
  const active=document.body.classList.toggle("focus-reading");
  event.currentTarget.setAttribute("aria-pressed",String(active));
  event.currentTarget.textContent=active?"Show navigation":"Focus reading";
 });
 document.getElementById("print-report").addEventListener("click",()=>window.print());
 main.addEventListener("click",async event=>{
  const button=event.target.closest("[data-copy-prompt],[data-select-prompt]");
  if(!button)return;
  const id=button.dataset.copyPrompt||button.dataset.selectPrompt;
  const input=document.getElementById(id);
  const message=document.getElementById(id.replace(/-prompt$/,"-status"));
  function selectManually(){
   input.focus();
   input.select();
   input.setSelectionRange(0,input.value.length);
  }
  if(button.dataset.selectPrompt){
   selectManually();
   message.textContent="Complete prompt selected. Press Ctrl+C (or Command+C) to copy.";
   return;
  }
  button.disabled=true;
  try{
   if(!navigator.clipboard?.writeText){
    selectManually();
    message.textContent="Automatic clipboard access is unavailable in this browser. The complete prompt is selected; press Ctrl+C (or Command+C).";
    return;
   }
   await navigator.clipboard.writeText(input.value);
   message.textContent="Copied the complete topic prompt. Paste it into your AI agent and attach any source notes it needs.";
  }catch(error){
   console.warn("Topic prompt clipboard copy failed:",error);
   selectManually();
   message.textContent="The browser blocked automatic copying. The complete prompt is selected; press Ctrl+C (or Command+C).";
  }finally{
   button.disabled=false;
  }
 });
 renderSearch();syncAnchor();
})();

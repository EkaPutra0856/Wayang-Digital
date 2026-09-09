const distance=(a,b)=>Math.hypot((a.x-b.x)*640,(a.y-b.y)*480);
export function countFingers(lm,label) {
  let count=0;
  if(distance(lm[4],lm[17])>=distance(lm[3],lm[17])*1.05&&
     distance(lm[4],lm[5])>=distance(lm[2],lm[5])*.75&&
     distance(lm[4],lm[0])>=distance(lm[3],lm[0])&&
     (label==='Left'?lm[4].x>=lm[3].x:lm[4].x<=lm[3].x)) count++;
  for(const [tip,pip,mcp] of [[8,6,5],[12,10,9],[16,14,13],[20,18,17]]) {
    if(distance(lm[tip],lm[0])>=distance(lm[pip],lm[0])&&
      distance(lm[tip],lm[0])>=distance(lm[mcp],lm[0])*1.15&&lm[tip].y<=lm[pip].y)count++;
  }
  return count;
}
export function toHands(result) {
  const candidates=(result.landmarks||[]).map((landmarks,i)=>{
    // Inference receives a mirrored frame, matching the desktop input.
    const raw=result.handedness[i][0];
    return {landmarks,label:raw.categoryName==='Left'?'Right':'Left',score:raw.score};
  }).filter(({landmarks:l})=>!(l[5].y>l[0].y&&l[17].y>l[0].y)).sort((a,b)=>b.score-a.score);
  const assigned=new Set();
  return candidates.slice(0,2).map(({landmarks:l,label})=>{
    if(assigned.has(label))label=label==='Right'?'Left':'Right';
    assigned.add(label);
    const xs=l.map(p=>p.x),ys=l.map(p=>p.y);
    return {label,landmarks:l.map(({x,y})=>({x,y})),count:countFingers(l,label),box:[Math.max(0,Math.min(...xs)-.03125),Math.max(0,Math.min(...ys)-.04167),Math.min(1,Math.max(...xs)+.03125),Math.min(1,Math.max(...ys)+.04167)]};
  });
}
export function voiceScene(text) {
  const keywords=[['koridor',4],['kelas',3],['sekolah',2],['al azhar',2],['alazhar',2],['pekalongan',2],['rumah',1],['makan',1],['taman',0]];
  const normalized=text.toLowerCase().replace(/[^a-z0-9 ]/g,' ');
  return keywords.find(([word])=>(' '+normalized+' ').includes(' '+word+' '))?.[1]??null;
}

'use strict';
// One-shot pigment transfer; generated donor is overwritten with the final wall.
const fs=require('node:fs'), crypto=require('node:crypto');
const {decodePNG,encodePNG,preview}=require('./finish_wall.js');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const source='artifacts/line-1/wall-v19.png',destination='artifacts/line-1/wall-v20.png';
if(fs.existsSync('dist/line-1/38.json'))throw Error('record exists');
const ancestorRaw=fs.readFileSync(source), donorRaw=fs.readFileSync(destination);
if(!ancestorRaw.equals(fs.readFileSync('artifacts/line-1/wall.png')))throw Error('ancestor mismatch');
if(JSON.parse(fs.readFileSync('dist/line-1/37.json')).image!=='https://api.imd.fun/artifacts/'+hash(ancestorRaw))throw Error('ancestor pin mismatch');
const ancestor=decodePNG(source),donor=decodePNG(destination);
if(ancestor.width!==1254||ancestor.height!==1254||ancestor.channels!==3)throw Error('ancestor format');
const out={...ancestor,pixels:Buffer.from(ancestor.pixels)};
// Bare upper rock, above the inherited cradle and left of the old upper panel.
const bounds=[410,110,570,172],crop=[0,Math.floor(donor.height*.19),donor.width,Math.ceil(donor.height*.70)];
let pigment=0;
for(let y=bounds[1];y<bounds[3];y++)for(let x=bounds[0];x<bounds[2];x++){
 const sx0=(x-bounds[0])*(crop[2]-crop[0])/(bounds[2]-bounds[0])+crop[0];
 const sx1=(x+1-bounds[0])*(crop[2]-crop[0])/(bounds[2]-bounds[0])+crop[0];
 const sy0=(y-bounds[1])*(crop[3]-crop[1])/(bounds[3]-bounds[1])+crop[1];
 const sy1=(y+1-bounds[1])*(crop[3]-crop[1])/(bounds[3]-bounds[1])+crop[1];
 let weight=0,coverage=0,sum=[0,0,0];
 for(let yy=Math.floor(sy0);yy<Math.ceil(sy1);yy++)for(let xx=Math.floor(sx0);xx<Math.ceil(sx1);xx++){
  const w=(Math.min(sx1,xx+1)-Math.max(sx0,xx))*(Math.min(sy1,yy+1)-Math.max(sy0,yy));
  const d=(yy*donor.width+xx)*donor.channels,r=donor.pixels[d],g=donor.pixels[d+1],b=donor.pixels[d+2];
  weight+=w;
  if(r>65&&((r-g>20&&r>b*1.5)||(r>110&&g>95&&b>70))){coverage+=w;for(let c=0;c<3;c++)sum[c]+=donor.pixels[d+c]*w;}
 }
 if(!coverage)continue;
 const i=(y*out.width+x)*3,alpha=.73*coverage/weight;
 for(let c=0;c<3;c++)out.pixels[i+c]=Math.round(out.pixels[i+c]*(1-alpha)+sum[c]/coverage*alpha);
 pigment++;
}
let changed=0;
for(let y=0;y<out.height;y++)for(let x=0;x<out.width;x++){
 const i=(y*out.width+x)*3;
 if(!out.pixels.subarray(i,i+3).equals(ancestor.pixels.subarray(i,i+3))){
  changed++;if(x<bounds[0]||x>=bounds[2]||y<bounds[1]||y>=bounds[3])throw Error('outside patch change');
 }
}
if(changed<300)throw Error('insufficient pigment');
const png=encodePNG(out),jpg=preview(out),digest=hash(png);
if(jpg.length>100000)throw Error('preview budget');
fs.writeFileSync(destination,png);fs.writeFileSync('artifacts/line-1/wall.png',png);
fs.writeFileSync('dist/line-1/38.jpg',jpg);
fs.writeFileSync('dist/line-1/38.json',JSON.stringify({name:'Tie Before the Trial',image:'https://api.imd.fun/artifacts/'+digest,attributes:[
 {trait_type:'Cave',value:'Roots'},{trait_type:'Wall',value:'Line 1'},{trait_type:'Number',value:38},
 {trait_type:'Left behind',value:'Bound Protocol'},
 {trait_type:'Meaning',value:'An ochre cord tied around three chalk pebbles keeps the comparison rules fixed before the trial.'},
 {trait_type:'One thing',value:'Reproducible benchmark evidence'}]},null,2)+'\n');
const review={wall:destination,width:out.width,height:out.height,format:'PNG RGB8',bytes:png.length,sha256:digest,
 preview:{path:'dist/line-1/38.jpg',width:512,height:512,format:'JPEG',bytes:jpg.length},
 ancestor:source,ancestor_sha256:hash(ancestorRaw),generated_donor_sha256:hash(donorRaw),
 bounds,donor_crop:crop,changed_pixels:changed,all_pixels_outside_bounds_identical:true,
 process:'Installed image generator produced isolated ochre/chalk pigment on black. Area-resampled pigment only onto bare upper rock; donor overwritten with final whole-wall PNG.',
 visual_review:{status:'pending local inspection',unmet_visual_requirements:[]},
 preview_location:'Explicit numbered-preview requirement places the only new JPEG in dist/line-1.'};
fs.writeFileSync('line-1/wall-review-38.json',JSON.stringify(review,null,2)+'\n');
console.log(JSON.stringify(review));

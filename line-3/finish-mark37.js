'use strict';
// Read-only ancestor and generated donor; write only this line's final outputs.
const fs = require('node:fs');
const crypto = require('node:crypto');
const {decodePNG, encodePNG, preview} = require('../line-1/wall-render/finish_wall.js');
const hash = b => crypto.createHash('sha256').update(b).digest('hex');
const ancestorPath = 'artifacts/line-3/wall-v19.png';
const outputPath = 'artifacts/line-3/wall-v20.png';
const ancestor = decodePNG(ancestorPath);
const donorBytes = fs.readFileSync(outputPath);
if (hash(donorBytes) !== '8d97ef47d304259389bb9159ebade16e9f3fbc4529e816b073ebc76f69226279') throw Error('one-time finishing requires the original generated donor, now replaced by the final wall');
const donor = decodePNG(outputPath);
if (ancestor.width !== donor.width || ancestor.height !== donor.height || ancestor.channels !== donor.channels) throw Error('image dimensions must match');
const result = {...ancestor, pixels: Buffer.from(ancestor.pixels)};
// The image tool placed its new motif here on bare rock, below all old marks.
const bounds = [893, 1117, 1005, 1182];
const [left, top, right, bottom] = bounds;
for (let y=top; y<bottom; y++) for(let x=left; x<right; x++) {
  const alpha = Math.max(0, Math.min(1, (x-left)/7, (right-1-x)/7, (y-top)/7, (bottom-1-y)/7));
  for(let c=0; c<result.channels; c++) {
    const at=(y*result.width+x)*result.channels+c;
    result.pixels[at] = Math.round(ancestor.pixels[at]*(1-alpha)+donor.pixels[at]*alpha);
  }
}
let changed=0, outside=0;
for(let y=0; y<result.height; y++) for(let x=0; x<result.width; x++) {
  const at=(y*result.width+x)*result.channels;
  if (!result.pixels.subarray(at,at+result.channels).equals(ancestor.pixels.subarray(at,at+result.channels))) {
    changed++;
    if(x<left || x>=right || y<top || y>=bottom) outside++;
  }
}
if(!changed || outside) throw Error('invalid additive edit');
const png=encodePNG(result), jpg=preview(result);
if(jpg.length>100000) throw Error('preview exceeds limit');
fs.writeFileSync(outputPath,png);
fs.unlinkSync('artifacts/line-3/wall.png');
fs.symlinkSync('wall-v20.png','artifacts/line-3/wall.png');
fs.writeFileSync('dist/line-3/37.jpg',jpg);
const stats={ancestor:ancestorPath,ancestor_sha256:hash(fs.readFileSync(ancestorPath)),
  donor_sha256:hash(donorBytes),patch_bounds_exclusive:bounds,changed_pixels:changed,
  changed_outside_patch:outside,wall:{path:outputPath,format:'PNG',width:result.width,
    height:result.height,color:'RGB8',bytes:png.length,sha256:hash(png)},
  preview:{path:'dist/line-3/37.jpg',format:'JPEG',width:512,height:512,bytes:jpg.length}};
fs.writeFileSync('line-3/round-37-image-check.json',JSON.stringify(stats,null,2)+'\n');
console.log(JSON.stringify(stats));

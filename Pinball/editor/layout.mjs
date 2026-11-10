// Fit the complete board, including its crest, into the actual canvas area.
// The caller supplies the measured padding; no reserved toolbar height or
// minimum zoom can silently crop a short window.
export function fitBoard(width,height,boardHeight,paddingX=32,paddingY=16){
 return Math.max(.05,Math.min(5,(width-paddingX)/128,(height-paddingY)/(boardHeight+24)));
}
export function followScroll({view_x,view_y,view_w,view_h},zoom,origin,width,height,scrollWidth,scrollHeight){
 const clamp=(n,limit)=>Math.max(0,Math.min(Math.max(0,limit),n));
 return {left:clamp(origin.x+(view_x+view_w/2)*zoom-width/2,scrollWidth-width),
         top:clamp(origin.y+(view_y+view_h/2)*zoom-height/2,scrollHeight-height)};
}

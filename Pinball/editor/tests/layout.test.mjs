import {test} from 'node:test';
import assert from 'node:assert/strict';
import {fitBoard,followScroll} from '../layout.mjs';
test('Fit includes the complete crest and board in short, narrow and tall workspaces',()=>{
 for(const [width,height] of [[700,350],[400,600],[240,300],[300,200],[1000,1200]])
  for(const boardHeight of [256,352,432,480]){
   const zoom=fitBoard(width,height,boardHeight);
   assert.ok(128*zoom+32<=width+1e-8);
   assert.ok((boardHeight+24)*zoom+16<=height+1e-8);
   assert.ok(zoom===5||Math.abs(128*zoom+32-width)<1e-8||Math.abs((boardHeight+24)*zoom+16-height)<1e-8,'use all available space on the limiting axis');
  }
 assert.ok(fitBoard(300,200,480)<.65,'a minimum zoom must not crop short windows');
});
test('Follow maps the C++ crop into the measured CSS viewport and clamps at each edge',()=>{
 const camera={view_x:20,view_y:180,view_w:86,view_h:72};
 const origin={x:16,y:68};
 assert.deepEqual(followScroll(camera,3,origin,300,400,416,1520),{left:55,top:516});
 const tall=followScroll(camera,3,origin,300,600,416,1520);
 assert.equal(tall.top,416,'a taller browser reveals equal extra space around the same C++ focus');
 assert.deepEqual(followScroll({...camera,view_y:-24},3,origin,800,800,416,1520),{left:0,top:0});
 assert.equal(followScroll({...camera,view_y:460},3,origin,300,400,416,1520).top,1120);
});

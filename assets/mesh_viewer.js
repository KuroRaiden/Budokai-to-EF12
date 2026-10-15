/* Offline textured mesh viewer. CPU skinning mirrors Blender deformation matrices.
   Source UVs can occupy tiles outside 0..1; fract repeats them for POT and NPOT textures. */
class MeshViewer {
 constructor(canvas){
  this.canvas=canvas;this.gl=canvas.getContext('webgl',{alpha:true,antialias:true});if(!this.gl)throw Error('WebGL is unavailable in this browser.');
  const gl=this.gl,compile=(type,src)=>{const s=gl.createShader(type);gl.shaderSource(s,src);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s};
  const vs=compile(gl.VERTEX_SHADER,'attribute vec3 aPos;attribute vec2 aUV;uniform mat4 uMVP;varying vec2 vUV;void main(){gl_Position=uMVP*vec4(aPos,1.0);vUV=aUV;}');
  const fs=compile(gl.FRAGMENT_SHADER,'precision mediump float;varying vec2 vUV;uniform sampler2D uTexture;uniform vec4 uColor;void main(){vec4 c=texture2D(uTexture,fract(vUV))*uColor;if(c.a<0.1)discard;gl_FragColor=c;}');
  this.program=gl.createProgram();gl.attachShader(this.program,vs);gl.attachShader(this.program,fs);gl.linkProgram(this.program);if(!gl.getProgramParameter(this.program,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(this.program));
  this.pos=gl.getAttribLocation(this.program,'aPos');this.uv=gl.getAttribLocation(this.program,'aUV');this.mvp=gl.getUniformLocation(this.program,'uMVP');this.color=gl.getUniformLocation(this.program,'uColor');
  this.parts=[];this.motion=null;this.data=null;this.loadVersion=0;this.lastFrame=-1;
 }
 disposeParts(){const gl=this.gl;for(const p of this.parts){gl.deleteBuffer(p.pb);gl.deleteBuffer(p.ub);gl.deleteTexture(p.texture)}this.parts=[];}
 async load(url){
  const request=++this.loadVersion,res=await fetch(url);if(!res.ok)throw Error('Character mesh could not be loaded.');const data=await res.json();if(request!==this.loadVersion)return;
  this.disposeParts();this.data=data;this.motion=null;this.lastFrame=-1;const gl=this.gl;let lo=[Infinity,Infinity,Infinity],hi=[-Infinity,-Infinity,-Infinity];
  for(const m of data.meshes){const base=new Float32Array(m.positions),positions=new Float32Array(base),uv=new Float32Array(m.uv);for(let i=0;i<base.length;i++) {lo[i%3]=Math.min(lo[i%3],base[i]);hi[i%3]=Math.max(hi[i%3],base[i])}
   const p={base,positions,joints:m.joints,weights:m.weights,pb:gl.createBuffer(),ub:gl.createBuffer(),texture:gl.createTexture(),count:base.length/3,color:m.texture?[1,1,1,1]:(m.color||[.8,.8,.8,1])};
   gl.bindBuffer(gl.ARRAY_BUFFER,p.pb);gl.bufferData(gl.ARRAY_BUFFER,positions,gl.DYNAMIC_DRAW);gl.bindBuffer(gl.ARRAY_BUFFER,p.ub);gl.bufferData(gl.ARRAY_BUFFER,uv,gl.STATIC_DRAW);
   gl.bindTexture(gl.TEXTURE_2D,p.texture);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([255,255,255,255]));gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);
   this.parts.push(p);
   if(m.texture){const image=new Image();image.onload=()=>{if(request!==this.loadVersion)return;gl.bindTexture(gl.TEXTURE_2D,p.texture);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,true);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,gl.RGBA,gl.UNSIGNED_BYTE,image)};image.src=new URL(m.texture,new URL(url,location.href)).href}
  }
  this.center=lo.map((v,i)=>(v+hi[i])/2);this.span=Math.max(...hi.map((v,i)=>v-lo[i]),1);
 }
 setMotion(motion){
  if(!this.data)return;
  const map=new Map(motion.bones.map((n,i)=>[n,i]));if(this.data.bones.some(n=>!map.has(n)))throw Error('Preview motion does not match this character mesh.');
  this.motion={...motion,frames:motion.frames.map(row=>this.data.bones.map(n=>row[map.get(n)]))};this.lastFrame=-1;
 }
 clearMotion(){this.motion=null;this.lastFrame=-1;}
 draw(frame,yaw,pitch,zoom,follow=true){
  const gl=this.gl,w=this.canvas.clientWidth,h=this.canvas.clientHeight,dpr=Math.min(devicePixelRatio||1,2);if(this.canvas.width!==Math.round(w*dpr)||this.canvas.height!==Math.round(h*dpr)){this.canvas.width=Math.round(w*dpr);this.canvas.height=Math.round(h*dpr)}
  gl.viewport(0,0,this.canvas.width,this.canvas.height);gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);if(!this.data)return;
  const f=this.motion?Math.floor(frame)%this.motion.frames.length:-1;
  if(f!==this.lastFrame||this.lastFrame===-1){
   const poseLo=[Infinity,Infinity,Infinity],poseHi=[-Infinity,-Infinity,-Infinity];
   for(const p of this.parts){if(f<0)p.positions.set(p.base);else{const mats=this.motion.frames[f];for(let i=0,v=0;i<p.base.length;i+=3,v++){
    const x=p.base[i],y=p.base[i+1],z=p.base[i+2];let xx=0,yy=0,zz=0,total=0;
    for(let k=0;k<4;k++){const weight=p.weights[v*4+k];if(!weight)continue;const m=mats[p.joints[v*4+k]];xx+=(m[0]*x+m[4]*y+m[8]*z+m[12])*weight;yy+=(m[1]*x+m[5]*y+m[9]*z+m[13])*weight;zz+=(m[2]*x+m[6]*y+m[10]*z+m[14])*weight;total+=weight}
    p.positions[i]=total?xx:x;p.positions[i+1]=total?yy:y;p.positions[i+2]=total?zz:z;
   }}for(let i=0;i<p.positions.length;i++){const axis=i%3;poseLo[axis]=Math.min(poseLo[axis],p.positions[i]);poseHi[axis]=Math.max(poseHi[axis],p.positions[i]);}gl.bindBuffer(gl.ARRAY_BUFFER,p.pb);gl.bufferSubData(gl.ARRAY_BUFFER,0,p.positions)}this.lastFrame=f;this.posedCenter=poseLo.map((v,i)=>(v+poseHi[i])/2);
  }
  const s=this.span,center=follow&&this.posedCenter?this.posedCenter:this.center,dist=s*3,eye=[center[0]+Math.sin(yaw)*Math.cos(pitch)*dist,center[1]+Math.cos(yaw)*Math.cos(pitch)*dist,center[2]+Math.sin(pitch)*dist];
  const norm=a=>{const n=Math.hypot(...a);return a.map(v=>v/n)},cross=(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],dot=(a,b)=>a.reduce((v,x,i)=>v+x*b[i],0);
  const z=norm(eye.map((v,i)=>v-center[i])),x=norm(cross([0,0,1],z)),y=cross(z,x),view=[x[0],y[0],z[0],0,x[1],y[1],z[1],0,x[2],y[2],z[2],0,-dot(x,eye),-dot(y,eye),-dot(z,eye),1];
  const top=s*.57/zoom,right=top*w/Math.max(h,1),near=.01,far=s*10,proj=[1/right,0,0,0,0,1/top,0,0,0,0,-2/(far-near),0,0,0,-(far+near)/(far-near),1],mvp=new Float32Array(16);
  for(let c=0;c<4;c++)for(let r=0;r<4;r++)for(let k=0;k<4;k++)mvp[c*4+r]+=proj[k*4+r]*view[c*4+k];
  gl.enable(gl.DEPTH_TEST);gl.disable(gl.CULL_FACE);gl.useProgram(this.program);gl.uniformMatrix4fv(this.mvp,false,mvp);gl.activeTexture(gl.TEXTURE0);
  for(const p of this.parts){gl.bindBuffer(gl.ARRAY_BUFFER,p.pb);gl.enableVertexAttribArray(this.pos);gl.vertexAttribPointer(this.pos,3,gl.FLOAT,false,0,0);gl.bindBuffer(gl.ARRAY_BUFFER,p.ub);gl.enableVertexAttribArray(this.uv);gl.vertexAttribPointer(this.uv,2,gl.FLOAT,false,0,0);gl.bindTexture(gl.TEXTURE_2D,p.texture);gl.uniform4fv(this.color,p.color);gl.drawArrays(gl.TRIANGLES,0,p.count)}
 }
}
window.MeshViewer=MeshViewer;

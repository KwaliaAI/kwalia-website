/*! Seph Blackwood, living portrait: light embed for a full-width band. No dependencies.
   window.SephPortrait = { mount(element), pause(), resume() }
   The element holds one <img> (the still: her portrait recomposed on a wide ground, shown with object-fit: cover).
   The script lays a WebGL canvas over it, framed exactly like the still, and bends that same picture:
   breath, sway, hair, earring, blink, eyes and head toward the pointer, idle glances, now and then a slight smirk.
   The mouth never opens. Cut down from puppet/src/seph.src.html (third version, 18 Nov 2026). */
(function (root) {
"use strict";

/* Landmarks, in pixels of the ORIGINAL 1024 x 1024 portrait. `crop` is the rectangle of that picture's plane the
   image file covers (x0, y0, w, h; wider than the portrait, since the ground is continued): it comes from the
   element's data-seph-crop, as printed by src/make_bands.py. The file's own resolution is free. */
var V = {
  crop: [0, 0, 1024, 1024],
  face: [400, 330],
  head:  { pivot: [545,640], fall: [592,820], xfall: [512,425,575] },      // xfall [cx, full half-width, zero half-width]: the continued ground stays still
  torso: { fall: [600,860], cx: 560, xfall: [540,470,600], breath: 3.2 },
  parallax: { c: [400,360], r: [120,140] },
  hair: [ // [cx,cy,rx,ry], lag gain, spring freq (rad/s), damping
    { r:[222,400, 62,170], gain:1.5, w:6.0, z:0.30 },
    { r:[770,380,105,190], gain:1.4, w:5.2, z:0.28 },
    { r:[800,570, 95, 75], gain:2.2, w:4.2, z:0.22 },
    { r:[385,690, 85,105], gain:1.8, w:4.6, z:0.25 },
    { r:[205,405, 45, 60], gain:2.4, w:3.8, z:0.20 },
    { r:[500, 60,220, 45], gain:0.8, w:6.5, z:0.35 }
  ],
  earring: { pivot:[684,378], seg:[682,386,677,444], radius:13, len:60, gain:3.0, w:7.5, z:0.10, hairDark:[15,13,16] },
  eyes: [
    { c:[315,343.5], angle:-11.5, hw:29, hc:12.5, hl:9,   lash:9,  lidZone:22, lowZone:14, skewU:0.0,  skewL:0.0,   pow:0.85,
      iris:[326,335,12], travel:[4.2,2.2], glint:[330,332.5,3.4,1.5,0.9], white:[205,208,206], shade:[176,172,170] },
    { c:[463,288.5], angle:-15.1, hw:45, hc:14,   hl:5.5, lash:10, lidZone:28, lowZone:16, skewU:0.15, skewL:-0.25, pow:0.85,
      iris:[476,278,15], travel:[5.8,2.5], glint:[474.5,277.5,1.9,1.7,0.9], white:[194,195,193], shade:[166,158,156] }
  ],
  irisColor: { mid:[100,78,62], rim:[45,33,30], pupil:[30,22,20] },
  feat: [ [468,212,48,20], [398,238,30,18], [300,290,32,15], [456,459,24,18], [364,468,15,15] ]  // brow outer, brow inner, other brow, mouth corners
};
var IDLE = { rot:1.35, x:3.8, y:1.6, pointerHold:2.0, fps:30, maxDpr:2, maxPx:2880,
             moodEvery:[24,50], moodFor:[3.5,6.5] };                       // seconds between small moods, seconds one lasts
/* Small moods only. brow px (+ up), lid 0..1 closes, smile -1..1, rot deg, hx/hy px, gx gaze. */
var MOODS = {
  neutral: {},
  smirk:   { browR:3.8, browRi:-1.7, browL:-0.7, lid:0.12, smileR:0.7, smileL:0.18, rot:1.1, hy:-1.4, gx:0.18 },
  stare:   { browR:-1.8, browRi:-1.0, browL:-1.2, lid:0.22, hy:0.8, rot:-0.4 }
};
var POSE_KEYS = ["browR","browRi","browL","lid","squint","smileR","smileL","rot","hx","hy","gx","gy"];

var VS = "attribute vec2 a;void main(){gl_Position=vec4(a,0.,1.);}";
var FS = [
"precision highp float;",
"uniform sampler2D uTex; uniform vec2 uRes; uniform vec3 uView; uniform vec4 uCrop;",
"uniform vec2 uHeadPivot; uniform vec4 uHead; uniform vec2 uHeadFall; uniform vec3 uHeadX;",
"uniform vec3 uTorso; uniform vec2 uBreath; uniform vec3 uTorsoX;",
"uniform vec4 uHairR[6]; uniform vec2 uHairO[6];",
"uniform vec4 uParR; uniform vec2 uParO;",
"uniform vec4 uFeatR[5]; uniform vec2 uFeatO[5];",
"uniform vec4 uEyeA[2]; uniform vec4 uEyeB[2]; uniform vec4 uEyeC[2]; uniform vec4 uEyeS[2]; uniform vec4 uEyeD[2];",
"uniform vec4 uEyeG[2]; uniform vec3 uEyeW[2]; uniform vec3 uEyeK[2]; uniform vec3 uEyeL[2];",
"uniform vec3 uIrisMid, uIrisRim, uPupil;",
"uniform vec4 uEar; uniform vec4 uEarSeg; uniform vec3 uHairDark;",
"float luma(vec3 c){ return dot(c, vec3(0.299,0.587,0.114)); }",
"vec3 tex(vec2 s){ return texture2D(uTex, clamp((s - uCrop.xy)/uCrop.zw, 0.0, 1.0)).rgb; }",
"float gs(vec2 p, vec4 r){ vec2 d=(p-r.xy)/r.zw; return exp(-dot(d,d)); }",
"float headW(vec2 p){ return (1.0 - smoothstep(uHeadFall.x, uHeadFall.y, p.y))*(1.0 - smoothstep(uHeadX.y, uHeadX.z, abs(p.x - uHeadX.x))); }",
"vec2 bodyDisp(vec2 p){",
"  float c = cos(uHead.z), s = sin(uHead.z);",
"  vec2 q = p - uHeadPivot;",
"  vec2 r = vec2(c*q.x - s*q.y, s*q.x + c*q.y)*(1.0+uHead.w) + uHeadPivot + uHead.xy;",
"  vec2 d = headW(p)*(r - p);",
"  float wt = smoothstep(uTorso.x, uTorso.y, p.y)*(1.0 - smoothstep(uTorsoX.y, uTorsoX.z, abs(p.x - uTorsoX.x)));",
"  d += wt*vec2((p.x - uTorso.z)*uBreath.x, uBreath.y);",
"  for (int i=0;i<6;i++) d += gs(p,uHairR[i])*uHairO[i];",
"  d += gs(p,uParR)*uParO;",
"  return d;",
"}",
"vec2 faceDisp(vec2 p){ vec2 d = vec2(0.); for (int i=0;i<5;i++) d += gs(p,uFeatR[i])*uFeatO[i]; return d; }",
"vec2 lidC(float u, vec4 B, vec4 C, float pw){",
"  float u1 = u + C.z*(1.0-u*u), u2 = u + C.w*(1.0-u*u);",
"  return vec2(-B.y*pow(max(1.0-u1*u1,0.0), pw), B.z*pow(max(1.0-u2*u2,0.0), pw));",
"}",
// One eye. The upper lash slides as a rigid band, lid skin stretches after it; inside the opening the iris is
// redrawn at the gaze offset (clipped by the lids) with a fixed catch-light.
"vec2 eyeWarp(vec2 p, vec4 A, vec4 B, vec4 C, vec4 S, vec4 D, vec4 G, vec3 sclW, vec3 sclS, vec3 L, inout vec4 ov){",
"  vec2 ax = A.zw; vec2 pr = vec2(-ax.y, ax.x);",
"  vec2 q = p - A.xy;",
"  float uu = dot(q,ax); float u = uu/B.x; float v = dot(q,pr);",
"  float T = C.x, TL = C.y;",
"  if (abs(u) >= 1.0 || v < -(B.y+T+4.0) || v > (B.z+TL+4.0)) return p;",
"  vec2 cv = lidC(u, B, C, D.w);",
"  float vc = cv.x, vl = cv.y;",
"  float t = B.w*smoothstep(0.0,0.25,1.0-abs(u));",
"  float open = vl - vc;",
"  float s = S.x > 0.0 ? S.x*(open + 0.14*B.y*smoothstep(0.0,0.3,1.0-abs(u))) : S.x*open;",
"  float sl = clamp(S.y*open, 0.0, max(open - max(s,0.0), 0.0));",
"  float cN = vc + s, lN = vl - sl;",
"  float nv = v;",
"  if (v < cN) {",
"    if (v > cN - t) nv = v - s;",
"    else if (v > vc - T) { float a0 = vc - T; nv = a0 + (v - a0)*(T - t)/max(T - t + s, 1.0); }",
"  } else if (v < lN) {",
"    float lifted = smoothstep(0.0, 0.03, -S.x);",
"    float moved = max(smoothstep(0.0, 0.9, length(G.xy)), lifted);",
"    vec3 scl = mix(sclS*mix(0.30, 1.0, smoothstep(0.0, 5.0, v - cN)), sclW, smoothstep(1.0, 8.0, v - cN));",
"    vec3 col = tex(p);",
"    col = mix(col, scl, lifted*(1.0 - smoothstep(-1.0, 1.5, v - vc)));",
"    col = mix(col, scl, moved*(1.0 - smoothstep(D.z+2.0, D.z+4.0, length(p - D.xy))));",
"    vec2 q2 = p - G.xy; float d1 = length(q2 - D.xy);",
"    float im = moved*(1.0 - smoothstep(D.z-0.9, D.z+0.9, d1));",
"    if (im > 0.0) {",
"      vec2 qq = q2 - A.xy; float su = dot(qq,ax)/B.x, sv = dot(qq,pr);",
"      vec2 sc = lidC(clamp(su,-1.0,1.0), B, C, D.w);",
"      float valid = smoothstep(0.5, 2.5, sv - sc.x)*smoothstep(0.0, 1.5, sc.y - sv)*step(abs(su), 1.0);",
"      float rr = d1/D.z;",
"      vec3 pi = mix(uPupil, uIrisMid, smoothstep(0.36,0.54,rr)); pi = mix(pi, uIrisRim, smoothstep(0.80,0.98,rr));",
"      vec3 ti = tex(q2);",
"      ti = mix(ti, pi, smoothstep(0.36, 0.50, luma(ti)));",
"      vec3 ic = mix(pi*mix(0.55, 1.0, smoothstep(0.0, 6.0, v - cN)), ti, valid);",
"      col = mix(col, ic, im);",
"    }",
"    vec2 gp = p - G.zw - G.xy*0.3; gp = vec2(dot(gp,ax), dot(gp,pr))/L.xy;",
"    col = mix(col, vec3(0.96,0.96,0.97), moved*L.z*(1.0 - smoothstep(0.55, 1.15, length(gp))));",
"    ov = vec4(col, moved);",
"  } else if (v < vl + TL) {",
"    float b0 = vl + TL; nv = b0 - (b0 - v)*TL/(TL + sl);",
"  }",
"  return A.xy + ax*uu + pr*nv;",
"}",
"float segD(vec2 p, vec2 a, vec2 b){ vec2 pa=p-a, ba=b-a; float h=clamp(dot(pa,ba)/dot(ba,ba),0.,1.); return length(pa-ba*h); }",
"float earM(vec2 p){ return 1.0 - smoothstep(uEar.w-4.0, uEar.w, segD(p, uEarSeg.xy, uEarSeg.zw)); }",
"void main(){",
"  vec2 fc = vec2(gl_FragCoord.x, uRes.y - gl_FragCoord.y);",
"  vec2 p = uView.xy + fc*uView.z;",
"  if (p.x < -80.0 || p.x > 1104.0) { gl_FragColor = vec4(tex(p), 1.0); return; }",        // plain ground: nothing to bend
"  vec2 b = p - bodyDisp(p - bodyDisp(p));",
"  vec2 f = b - faceDisp(b - faceDisp(b));",
"  vec4 eov = vec4(0.);",
"  vec2 s = eyeWarp(f, uEyeA[0], uEyeB[0], uEyeC[0], uEyeS[0], uEyeD[0], uEyeG[0], uEyeW[0], uEyeK[0], uEyeL[0], eov);",
"  s = eyeWarp(s, uEyeA[1], uEyeB[1], uEyeC[1], uEyeS[1], uEyeD[1], uEyeG[1], uEyeW[1], uEyeK[1], uEyeL[1], eov);",
"  vec3 col = tex(s);",
"  float mr = earM(s);",                       // earring: paint out the resting one, draw it again swung about its hook
"  if (mr > 0.0) col = mix(col, uHairDark, mr*smoothstep(0.16,0.30,luma(col)));",
"  float ca = cos(uEar.z), sa = sin(uEar.z);",
"  vec2 eq = s - uEar.xy; eq = vec2(ca*eq.x + sa*eq.y, -sa*eq.x + ca*eq.y) + uEar.xy;",
"  float m2 = earM(eq);",
"  if (m2 > 0.0) { vec3 c2 = tex(eq); col = mix(col, c2, m2*smoothstep(0.16,0.30,luma(c2))); }",
"  col = mix(col, eov.rgb, eov.a);",
"  gl_FragColor = vec4(col, 1.0);",
"}"].join("\n");

var TAU = Math.PI*2;
function clamp(v, a, b){ return Math.max(a, Math.min(b, v)); }
function rgb(a){ return [a[0]/255, a[1]/255, a[2]/255]; }
function flat(a){ var o = []; (function w(x){ for (var i=0;i<x.length;i++) { if (x[i] && x[i].length !== undefined) w(x[i]); else o.push(x[i]); } })(a); return new Float32Array(o); }
function between(r){ return r[0] + (r[1]-r[0])*Math.random(); }
function zeroPose(){ var o = {}; POSE_KEYS.forEach(function(k){ o[k] = 0; }); return o; }
function fullPose(name){ var o = zeroPose(), m = MOODS[name] || {}; POSE_KEYS.forEach(function(k){ if (k in m) o[k] = m[k]; }); return o; }

var box = null, img = null, canvas = null, gl = null, prog = null, locs = {};
var mounted = false, glReady = false, failed = false, lost = false, live = false;
var visible = false, userPaused = false, reduced = false, running = false, raf = 0, last = 0, lastDraw = 0;
var mqReduce = null, compileTimer = 0, parallelCompile = null;

/* ---- animation state ---- */
var S = {
  t: 0, wake: 0, pose: zeroPose(), from: zeroPose(), to: zeroPose(), moodT: 1, moodNext: 0, moodEnd: 0,
  blinkNext: 1.8, blinkT: -1, blinkAgain: false, blink: 0,
  glanceNext: 3.2, glance: [0,0], sacNext: 0.9, sac: [0,0], sacCur: [0,0],
  pointer: null, eye: [0,0], headLook: [0,0],
  hair: V.hair.map(function(){ return { x:0, y:0, vx:0, vy:0 }; }), hairO: V.hair.map(function(){ return [0,0]; }),
  ear: { x:0, v:0 }, earAng: 0
};
S.moodNext = between([12, 22]);

function headPose(){
  var t = S.t, P = S.pose, k = S.wake;
  var breath = Math.sin(TAU*t/3.9 + 0.35*Math.sin(TAU*t/17));
  var rot = k*IDLE.rot*(0.9*Math.sin(TAU*t/7.3) + 0.5*Math.sin(TAU*t/12.7+1.3) + 0.25*Math.sin(TAU*t/3.9+0.5));
  var hx = k*IDLE.x*(Math.sin(TAU*t/9.1+2.0) + 0.5*Math.sin(TAU*t/5.3));
  var hy = k*(IDLE.y*Math.sin(TAU*t/6.7+0.7) - 1.4*(0.5+0.5*breath));
  rot += P.rot + 1.3*S.headLook[0];
  hx += P.hx + 7*S.headLook[0];
  hy += P.hy + 4.5*S.headLook[1];
  return { rot: rot*Math.PI/180, hx: hx, hy: hy, breath: k*(0.5+0.5*breath) };
}
function headDispAt(H, c){
  var pv = V.head.pivot, qx = c[0]-pv[0], qy = c[1]-pv[1], co = Math.cos(H.rot), si = Math.sin(H.rot);
  return [ (co*qx - si*qy) + pv[0] + H.hx - c[0], (si*qx + co*qy) + pv[1] + H.hy - c[1] ];
}
function mood(name){ S.from = {}; POSE_KEYS.forEach(function(k){ S.from[k] = S.pose[k]; }); S.to = fullPose(name); S.moodT = 0; }

function step(dt){
  S.t += dt; var t = S.t, i;
  var wk = Math.min(1, t/1.8); S.wake = wk*wk*(3-2*wk);            // she starts exactly as the still and comes alive over ~2 s
  if (S.moodT < 1) { S.moodT = Math.min(1, S.moodT + dt/0.45); var e = S.moodT, w = e*e*(3-2*e);
    POSE_KEYS.forEach(function(k){ S.pose[k] = S.from[k] + (S.to[k]-S.from[k])*w; }); }
  if (S.moodEnd && t >= S.moodEnd) { S.moodEnd = 0; mood("neutral"); S.moodNext = t + between(IDLE.moodEvery); }
  else if (!S.moodEnd && t >= S.moodNext) { mood(Math.random() < 0.7 ? "smirk" : "stare"); S.moodEnd = t + between(IDLE.moodFor); }
  // blink
  if (S.blinkT < 0 && t >= S.blinkNext) S.blinkT = 0;
  if (S.blinkT >= 0) {
    S.blinkT += dt; var b = S.blinkT;
    S.blink = b < 0.07 ? Math.sin((b/0.07)*Math.PI/2) : b < 0.10 ? 1 : b < 0.24 ? 0.5+0.5*Math.cos(((b-0.10)/0.14)*Math.PI) : 0;
    if (b >= 0.24) { S.blinkT = -1; S.blink = 0;
      if (!S.blinkAgain && Math.random() < 0.18) { S.blinkAgain = true; S.blinkNext = t + 0.09; }
      else { S.blinkAgain = false; S.blinkNext = t + 2 + 4*Math.random(); } }
  }
  // glances at nothing in particular, eye-led
  if (t >= S.glanceNext) {
    var away = Math.random() < 0.75;
    S.glance = away ? [(Math.random()*2-1)*0.8, (Math.random()*2-1)*0.5] : [0,0];
    S.glanceNext = t + (away ? 1.0 + 2.2*Math.random() : 2.5 + 4.5*Math.random());
    if (away && Math.random() < 0.5 && S.blinkT < 0) S.blinkNext = Math.min(S.blinkNext, t + 0.05);
  }
  // saccades: tiny quick jumps so the eyes are never dead still
  if (t >= S.sacNext) { S.sac = [(Math.random()*2-1)*0.12, (Math.random()*2-1)*0.08]; S.sacNext = t + 0.45 + 1.3*Math.random(); }
  // who has the eyes: a pointer or touch that moved in the last two seconds, else her own glances
  var tgt = S.glance;
  if (S.pointer && performance.now() - S.pointer.at < IDLE.pointerHold*1000) tgt = S.pointer.p;
  var ke = 1 - Math.exp(-dt/0.06), kh = 1 - Math.exp(-dt/0.26), ks = 1 - Math.exp(-dt/0.018);
  for (i = 0; i < 2; i++) { S.eye[i] += (tgt[i]*S.wake - S.eye[i])*ke; S.headLook[i] += (S.eye[i]-S.headLook[i])*kh; S.sacCur[i] += (S.sac[i]*S.wake - S.sacCur[i])*ks; }
  // hair and earring: springs that chase the head, so they lag and overshoot
  var H = headPose();
  V.hair.forEach(function(h, n){
    var st = S.hair[n], hd = headDispAt(H, h.r);
    st.vx += (h.w*h.w*(hd[0]-st.x) - 2*h.z*h.w*st.vx)*dt; st.vy += (h.w*h.w*(hd[1]-st.y) - 2*h.z*h.w*st.vy)*dt;
    st.x += st.vx*dt; st.y += st.vy*dt;
    S.hairO[n] = [ h.gain*(st.x-hd[0]) + S.wake*1.3*Math.sin(TAU*t/(4.3+n*0.9) + n*1.7),
                   h.gain*(st.y-hd[1])*0.6 + S.wake*0.6*Math.sin(TAU*t/(5.1+n*0.7) + n) ];
  });
  var E = V.earring, ed = headDispAt(H, E.pivot), es = S.ear;
  es.v += (E.w*E.w*(ed[0]-es.x) - 2*E.z*E.w*es.v)*dt; es.x += es.v*dt;
  S.earAng = clamp(-E.gain*(es.x-ed[0])/E.len - H.rot*0.9 + S.wake*0.03*Math.sin(TAU*t/2.3), -0.35, 0.35);
}

/* ---- WebGL ---- */
function U(n){ return (n in locs) ? locs[n] : (locs[n] = gl.getUniformLocation(prog, n)); }
function initGL(){
  try {
    if (!gl) {
      var opts = { antialias:false, alpha:false, depth:false, stencil:false, powerPreference:"low-power" };
      gl = canvas.getContext("webgl", opts) || canvas.getContext("experimental-webgl", opts);
      if (!gl) return false;
      parallelCompile = gl.getExtension("KHR_parallel_shader_compile");
      // Checking COMPILE_STATUS here would wait synchronously for the GPU.
      var mk = function(type, src){ var s = gl.createShader(type); gl.shaderSource(s, src); gl.compileShader(s); return s; };
      prog = gl.createProgram(); locs = {};
      gl.attachShader(prog, mk(gl.VERTEX_SHADER, VS)); gl.attachShader(prog, mk(gl.FRAGMENT_SHADER, FS)); gl.linkProgram(prog);
    }
    if (parallelCompile && !gl.getProgramParameter(prog, parallelCompile.COMPLETION_STATUS_KHR)) {
      if (!compileTimer) compileTimer = root.setTimeout(function(){ compileTimer = 0; update(); }, 32);
      return null; // Keep the still and yield while the driver compiles.
    }
    if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) throw new Error("link");
    gl.useProgram(prog);
    gl.bindBuffer(gl.ARRAY_BUFFER, gl.createBuffer());
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
    var la = gl.getAttribLocation(prog, "a"); gl.enableVertexAttribArray(la); gl.vertexAttribPointer(la, 2, gl.FLOAT, false, 0, 0);
    gl.bindTexture(gl.TEXTURE_2D, gl.createTexture());
    var srcTex = img, maxT = gl.getParameter(gl.MAX_TEXTURE_SIZE) || 2048;
    if (img.naturalWidth > maxT) {                                                // old phones: bring the wide picture under the texture limit
      srcTex = document.createElement("canvas"); srcTex.width = maxT; srcTex.height = Math.max(1, Math.round(img.naturalHeight*maxT/img.naturalWidth));
      srcTex.getContext("2d").drawImage(img, 0, 0, srcTex.width, srcTex.height);
    }
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGB, gl.RGB, gl.UNSIGNED_BYTE, srcTex);    // throws if the picture is cross-origin without CORS
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    if (gl.getError() !== gl.NO_ERROR) throw new Error("gl");
    // everything that never changes
    gl.uniform1i(U("uTex"), 0);
    gl.uniform4fv(U("uCrop"), V.crop);
    gl.uniform2fv(U("uHeadPivot"), V.head.pivot); gl.uniform2fv(U("uHeadFall"), V.head.fall); gl.uniform3fv(U("uHeadX"), V.head.xfall);
    gl.uniform3f(U("uTorso"), V.torso.fall[0], V.torso.fall[1], V.torso.cx); gl.uniform3fv(U("uTorsoX"), V.torso.xfall);
    gl.uniform4fv(U("uHairR"), flat(V.hair.map(function(h){ return h.r; })));
    gl.uniform4f(U("uParR"), V.parallax.c[0], V.parallax.c[1], V.parallax.r[0], V.parallax.r[1]);
    gl.uniform4fv(U("uFeatR"), flat(V.feat));
    var A = [], B = [], C = [], D = [], W = [], K = [], L = [];
    V.eyes.forEach(function(e){ var a = e.angle*Math.PI/180;
      A.push(e.c[0], e.c[1], Math.cos(a), Math.sin(a)); B.push(e.hw, e.hc, e.hl, e.lash); C.push(e.lidZone, e.lowZone, e.skewU, e.skewL);
      D.push(e.iris[0], e.iris[1], e.iris[2], e.pow); W.push(rgb(e.white)); K.push(rgb(e.shade)); L.push(e.glint[2], e.glint[3], e.glint[4]); });
    gl.uniform4fv(U("uEyeA"), flat(A)); gl.uniform4fv(U("uEyeB"), flat(B)); gl.uniform4fv(U("uEyeC"), flat(C)); gl.uniform4fv(U("uEyeD"), flat(D));
    gl.uniform3fv(U("uEyeW"), flat(W)); gl.uniform3fv(U("uEyeK"), flat(K)); gl.uniform3fv(U("uEyeL"), flat(L));
    gl.uniform3fv(U("uIrisMid"), rgb(V.irisColor.mid)); gl.uniform3fv(U("uIrisRim"), rgb(V.irisColor.rim)); gl.uniform3fv(U("uPupil"), rgb(V.irisColor.pupil));
    gl.uniform4fv(U("uEarSeg"), V.earring.seg); gl.uniform3fv(U("uHairDark"), rgb(V.earring.hairDark));
    return true;
  } catch (e) { gl = null; return false; }
}
var quality = 1, qN = 0, qT = 0;                                  // drawing resolution is stepped down on machines that cannot hold the frame rate
var F = { ox: 0, oy: 0, s: 1 };                                   // framing: picture px at the canvas's top-left corner, CSS px per picture px
function resize(){
  if (!canvas || !box) return;
  var r = canvas.getBoundingClientRect(); if (r.width < 2 || r.height < 2) return;
  var dpr = Math.min(root.devicePixelRatio || 1, IDLE.maxDpr, IDLE.maxPx/r.width)*quality;
  var w = Math.max(2, Math.round(r.width*dpr)), h = Math.max(2, Math.round(r.height*dpr));
  if (canvas.width !== w || canvas.height !== h) { canvas.width = w; canvas.height = h; }
  // the still is shown with object-fit: cover and an object-position in percent: frame the canvas the same way
  var pos = [0.5, 0.5];
  try { var m = (root.getComputedStyle(img).objectPosition || "").match(/(-?[\d.]+)%\s+(-?[\d.]+)%/); if (m) pos = [parseFloat(m[1])/100, parseFloat(m[2])/100]; } catch (e) {}
  var s = Math.max(r.width/V.crop[2], r.height/V.crop[3]);
  F.s = s; F.ox = V.crop[0] + (V.crop[2] - r.width/s)*pos[0]; F.oy = V.crop[1] + (V.crop[3] - r.height/s)*pos[1];
}
function render(){
  var W = canvas.width, Hh = canvas.height, P = S.pose, H = headPose();
  gl.viewport(0, 0, W, Hh);
  gl.uniform2f(U("uRes"), W, Hh);
  gl.uniform3f(U("uView"), F.ox, F.oy, canvas.getBoundingClientRect().width/(F.s*W));
  gl.uniform4f(U("uHead"), H.hx, H.hy, H.rot, 0);
  gl.uniform2f(U("uBreath"), 0.004*H.breath, -V.torso.breath*H.breath);
  gl.uniform2fv(U("uHairO"), flat(S.hairO));
  gl.uniform2f(U("uParO"), 5*S.headLook[0], 3.5*S.headLook[1]);
  gl.uniform2fv(U("uFeatO"), flat([[0, -P.browR], [0, -(P.browR + P.browRi)], [0, -P.browL], [2.5*P.smileR, -6.5*P.smileR], [-1.0*P.smileL, -3.5*P.smileL]]));
  var gx = clamp(S.eye[0] + P.gx + S.sacCur[0], -1.15, 1.15), gy = clamp(S.eye[1] + P.gy + S.sacCur[1], -1.15, 1.15);
  var lidBase = P.lid + 0.20*Math.max(gy, 0) - 0.03*Math.max(-gy, 0);
  var lid = clamp(lidBase + S.blink*(1 - lidBase), -0.4, 1);
  var G = [], Ss = [];
  V.eyes.forEach(function(e){ var a = e.angle*Math.PI/180, ax = Math.cos(a), ay = Math.sin(a), ox = gx*e.travel[0], oy = gy*e.travel[1];
    G.push(ax*ox - ay*oy, ay*ox + ax*oy, e.glint[0], e.glint[1]); Ss.push(lid, P.squint, 0, 0); });
  gl.uniform4fv(U("uEyeG"), flat(G)); gl.uniform4fv(U("uEyeS"), flat(Ss));
  gl.uniform4f(U("uEar"), V.earring.pivot[0], V.earring.pivot[1], S.earAng, V.earring.radius);
  gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
}

/* ---- run only when it is worth running ---- */
function frame(now){
  raf = root.requestAnimationFrame(frame);
  var step30 = 1000/IDLE.fps, el = now - lastDraw;
  if (el < step30 - 1.5) return;                                   // frame-rate cap
  lastDraw = el > 2*step30 ? now : lastDraw + step30;
  var dt = Math.min(0.1, Math.max(0, (now - last)/1000)); last = now;
  while (dt > 1e-5) { var d = Math.min(dt, 1/60); step(d); dt -= d; }
  render();
  if (++qN === 15) qT = now;                                       // skip the warm-up, then time 30 frames
  else if (qN === 45) { var fps = 30000/Math.max(1, now - qT); qN = 0;
    if (fps < 22 && quality > 0.4) { quality = Math.max(0.4, quality*0.75); resize(); } }
  if (!live) { live = true; box.classList.add("is-live"); }       // the CSS fades the canvas in over the still
}
function start(){
  if (running) return;
  if (!glReady) {
    if (!(img.complete && img.naturalWidth > 0)) return;           // the still has not arrived yet: its load event calls update()
    resize();
    var ready = initGL();
    if (ready === null) return;
    if (!ready) { failed = true; return; }                         // no WebGL: the still stays, nothing else happens
    glReady = true;
  }
  running = true; qN = 0; last = lastDraw = performance.now(); raf = root.requestAnimationFrame(frame);
}
function stop(){ if (compileTimer) { root.clearTimeout(compileTimer); compileTimer = 0; } if (running) { running = false; root.cancelAnimationFrame(raf); } }
function update(){
  if (!mounted) return;
  var want = visible && !document.hidden && !userPaused && !reduced && !failed && !lost;
  if (want) start(); else stop();
  if ((reduced || failed || lost) && live) { live = false; box.classList.remove("is-live"); }   // back to the plain still
}
function setPointer(x, y, touch){
  if (!running) return;
  var r = canvas.getBoundingClientRect(), b = box.getBoundingClientRect();
  var fx = r.left + (V.face[0]-F.ox)*F.s, fy = r.top + (V.face[1]-F.oy)*F.s;
  var rx = Math.max(260, root.innerWidth*0.30), ry = Math.max(b.height*0.7, root.innerHeight*0.36);
  var g = (y >= b.top && y <= b.bottom) ? 1 : 0.6;                 // fully over the band, gently from the rest of the page
  S.pointer = { p: [g*clamp((x - fx)/rx, -1, 1), g*clamp((y - fy)/ry, -1, 1)], at: performance.now(), touch: !!touch };
}
function onPointer(e){ if (e.pointerType !== "touch") setPointer(e.clientX, e.clientY, false); }
function onTouch(e){ var t = e.touches && e.touches[0]; if (t) setPointer(t.clientX, t.clientY, true); }
function onTouchEnd(){ if (S.pointer && S.pointer.touch) S.pointer.at = performance.now() - (IDLE.pointerHold*1000 - 500); }   // let go half a second after the finger lifts

function mount(el){
  if (mounted || !el) return api;
  img = el.querySelector("img"); if (!img) return api;
  box = el; mounted = true;
  var c = (el.getAttribute("data-seph-crop") || "").split(",").map(Number);
  if (c.length === 4 && c[2] > 0 && c[3] > 0) V.crop = c;
  canvas = document.createElement("canvas");
  canvas.setAttribute("aria-hidden", "true"); canvas.setAttribute("role", "presentation"); canvas.tabIndex = -1;
  img.parentNode.insertBefore(canvas, img.nextSibling);
  canvas.addEventListener("webglcontextlost", function(e){ e.preventDefault(); lost = true; glReady = false; gl = null; prog = null; update(); }, false);
  canvas.addEventListener("webglcontextrestored", function(){ lost = false; update(); }, false);
  if (root.matchMedia) {
    mqReduce = root.matchMedia("(prefers-reduced-motion: reduce)"); reduced = mqReduce.matches;
    var onMq = function(){ reduced = mqReduce.matches; update(); };
    if (mqReduce.addEventListener) mqReduce.addEventListener("change", onMq); else if (mqReduce.addListener) mqReduce.addListener(onMq);
  }
  if ("IntersectionObserver" in root) {
    new IntersectionObserver(function(es){ visible = es[es.length-1].isIntersecting; update(); }, { threshold: 0.05 }).observe(box);
  } else visible = true;
  if ("ResizeObserver" in root) new ResizeObserver(resize).observe(box);
  root.addEventListener("resize", resize);
  document.addEventListener("visibilitychange", update);
  img.addEventListener("load", update);
  // all listeners are passive and on the window: nothing here can block scrolling or steal a tap
  var pv = { passive: true };
  root.addEventListener("pointermove", onPointer, pv);
  root.addEventListener("touchstart", onTouch, pv); root.addEventListener("touchmove", onTouch, pv);
  root.addEventListener("touchend", onTouchEnd, pv); root.addEventListener("touchcancel", onTouchEnd, pv);
  update();
  return api;
}
var api = {
  mount: mount,
  pause: function(){ userPaused = true; update(); },
  resume: function(){ userPaused = false; update(); },
  // test hook, not part of the API: _poke("blink") or _poke("smirk" | "stare") shows that thing now
  _poke: function(what){ if (what === "blink") S.blinkNext = S.t; else if (MOODS[what]) { mood(what); S.moodEnd = S.t + 4; } }
};
root.SephPortrait = api;

// convenience: <div data-seph-portrait><img ...></div> mounts itself
function auto(){ var el = document.querySelector("[data-seph-portrait]"); if (el) mount(el); }
if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto); else auto();
})(window);

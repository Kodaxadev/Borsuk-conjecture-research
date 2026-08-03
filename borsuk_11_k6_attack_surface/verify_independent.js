#!/usr/bin/env node
"use strict";
const fs=require("fs"),path=require("path"),crypto=require("crypto");
const ROOT=__dirname,N=11,K=6,BASE=(1<<6)-1;
const CENTERS=[0,63,455,748,858,945,1241,1396,1450,1635,1686,1805];
function pc(x){let n=x>>>0,c=0;while(n){n&=n-1;c++;}return c;}
const vs=[];for(let x=0;x<(1<<N);x++)if(pc(x)%2===0&&pc(x)<=K&&pc(x^BASE)<=K)vs.push(x);
if(vs.length!==692)throw Error("vertex count");
const edges=[];for(let i=0;i<vs.length;i++)for(let j=i+1;j<vs.length;j++)if(pc(vs[i]^vs[j])===K)edges.push([vs[i],vs[j]]);
if(edges.length!==104606)throw Error(`edge count ${edges.length}`);
const edgeText=edges.map(e=>`${e[0]},${e[1]}\n`).join("");
const graphHash=crypto.createHash("sha256").update(edgeText).digest("hex");
const partial=JSON.parse(fs.readFileSync(path.join(ROOT,"partial_witness.json"),"utf8"));
if(graphHash!==partial.expected.trim_graph_sha256)throw Error("graph hash");
for(let i=0;i<CENTERS.length;i++)for(let j=i+1;j<CENTERS.length;j++)if(pc(CENTERS[i]^CENTERS[j])!==6)throw Error("clique");
const assigned=new Map(Object.entries(partial.assigned).map(([v,c])=>[Number(v),c]));
let bad=0;for(const [a,b] of edges)if(assigned.has(a)&&assigned.has(b)&&assigned.get(a)===assigned.get(b))bad++;
if(bad)throw Error(`partial conflicts ${bad}`);
const uncolored=partial.uncolored, uset=new Set(uncolored);
const core=edges.filter(([a,b])=>uset.has(a)&&uset.has(b));
if(core.length!==3015)throw Error("core edges");
const coreHash=crypto.createHash("sha256").update(core.map(e=>`${e[0]},${e[1]}\n`).join("")).digest("hex");
if(coreHash!==partial.expected.core_sha256)throw Error("core hash");
console.log(JSON.stringify({
 status:"PASS",method:"independent all-pairs enumeration",
 trim_vertices:vs.length,trim_edges:edges.length,
 partial_assigned:assigned.size,core_vertices:uncolored.length,
 core_edges:core.length,graph_sha256:graphHash,core_sha256:coreHash
},null,2));

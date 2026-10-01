// Legacy standalone MCP development harness.
// The production OpenAI public plugin uses nexus/main.py + nexus/mcp_server.py.
// Keep this file for local SDK experiments; do not treat its tool surface as the directory contract.

import { createServer } from "node:http";
import { randomUUID } from "node:crypto";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { z } from "zod";

const PORT = Number(process.env.PORT || 8787);
const MCP_PATH = "/mcp";
const API_TOKEN = process.env.NEXUS_API_TOKEN || "";
const MAX_BODY = 1_000_000;

const domains = [
  ["research", "Research", ["literature", "llm_research", "patents", "experiments", "fact_checking", "synthesis"]],
  ["engineering", "Engineering", ["architecture", "coding", "debugging", "testing", "devops", "code_review"]],
  ["business", "Business", ["market_research", "product", "strategy", "sales", "operations", "competitive_intelligence"]],
  ["data", "Data & Knowledge", ["rag", "etl", "sql", "analytics", "knowledge_graph", "document_intelligence"]],
  ["infrastructure", "Infrastructure", ["gpu", "cloud", "containers", "kubernetes", "reliability", "cost_optimization"]],
  ["security", "Security", ["threat_analysis", "dependency_risk", "incident_review", "secrets", "compliance", "audit"]],
  ["productivity", "Productivity", ["email", "documents", "meetings", "calendar", "summaries", "presentations"]],
  ["finance", "Finance", ["budgeting", "expenses", "invoices", "forecasting", "procurement", "cost_analysis"]],
  ["career", "Career", ["jobs", "cv", "portfolio", "interview", "networking", "skills"]],
  ["personal", "Personal", ["travel", "learning", "planning", "shopping", "household", "organization"]]
].map(([id,name,capabilities],di)=>({
  id,name,capabilities,
  agents:Array.from({length:10},(_,i)=>({id:`A${di*10+i+1}`,status:"available"}))
}));

const missions = new Map();

function jsonResult(data, text) {
  return { structuredContent: data, content: [{ type: "text", text }] };
}
function authOk(req) {
  if (!API_TOKEN) return true;
  return req.headers.authorization === `Bearer ${API_TOKEN}`;
}
function classify(objective) {
  const s=objective.toLowerCase();
  const scores=new Map(domains.map(d=>[d.id,0]));
  const words={
    research:["research","paper","study","llm","model","literature","patent"],
    engineering:["code","build","implement","debug","test","api","software","app"],
    business:["market","business","product","customer","competitor","sales"],
    data:["data","rag","sql","dataset","analytics","document","etl"],
    infrastructure:["gpu","cloud","deploy","docker","kubernetes","server","latency"],
    security:["security","risk","vulnerability","audit","threat","secret"],
    productivity:["email","document","meeting","calendar","presentation","summary"],
    finance:["budget","cost","invoice","expense","finance","forecast"],
    career:["job","career","resume","cv","interview","portfolio"],
    personal:["travel","learn","shopping","personal","plan","household"]
  };
  for(const [id,terms] of Object.entries(words)) for(const t of terms) if(s.includes(t)) scores.set(id,scores.get(id)+1);
  let chosen=[...scores.entries()].filter(([,v])=>v>0).sort((a,b)=>b[1]-a[1]).slice(0,4).map(([id])=>id);
  if(!chosen.length) chosen=["research","productivity"];
  if((s.includes("deploy")||s.includes("code"))&&!chosen.includes("security")) chosen.push("security");
  return chosen.slice(0,5);
}
function plan(objective, priority) {
  const selected=classify(objective);
  return selected.map((id,i)=>{
    const d=domains.find(x=>x.id===id);
    return {step:i+1,domain:id,orchestrator:`${d.name} Orchestrator`,agent:d.agents[i%d.agents.length].id,status:"planned"};
  });
}
function makeServer() {
  const server = new McpServer(
    { name: "nexus-100", version: "1.0.0" },
    { instructions: "NEXUS-100 is a governed multi-orchestrator control plane. Use plan_mission before run_mission for complex objectives. Prefer read-only inspection. Consequential external writes, deployment, deletion, spending, or communication must remain approval-gated and must never be represented as completed unless an authorized executor actually confirms success." }
  );

  server.registerTool("get_system_status",{
    title:"Get NEXUS-100 system status",
    description:"Inspect the NEXUS-100 control plane, domains and registered specialist count.",
    inputSchema:{},
    outputSchema:{status:z.string(),domains:z.number(),agents:z.number(),missions:z.number()},
    annotations:{readOnlyHint:true,openWorldHint:false,destructiveHint:false}
  },async()=>jsonResult({status:"healthy",domains:domains.length,agents:domains.reduce((n,d)=>n+d.agents.length,0),missions:missions.size},"NEXUS-100 control plane is healthy."));

  server.registerTool("list_domains",{
    title:"List NEXUS-100 domains",
    description:"List domain orchestrators, capabilities and specialist agent IDs.",
    inputSchema:{},
    annotations:{readOnlyHint:true,openWorldHint:false,destructiveHint:false}
  },async()=>jsonResult({domains},"NEXUS-100 has 10 domain orchestrators and 100 registered specialist slots."));

  server.registerTool("plan_mission",{
    title:"Plan a multi-agent mission",
    description:"Create a governed execution plan and route an objective to the smallest useful set of domain orchestrators. This does not perform external actions.",
    inputSchema:{objective:z.string().min(3).max(4000),priority:z.enum(["low","normal","high","critical"]).default("normal")},
    annotations:{readOnlyHint:true,openWorldHint:false,destructiveHint:false}
  },async({objective,priority})=>{
    const route=plan(objective,priority);
    return jsonResult({objective,priority,route,requiresApproval:false},`Planned ${route.length} orchestrator hops: ${route.map(x=>x.orchestrator).join(" → ")}.`);
  });

  server.registerTool("run_mission",{
    title:"Start a NEXUS-100 mission",
    description:"Create a tracked NEXUS-100 mission from an objective. It activates a routed task graph in the control plane; it does not claim external side effects that are not backed by configured executors.",
    inputSchema:{objective:z.string().min(3).max(4000),priority:z.enum(["low","normal","high","critical"]).default("normal"),dryRun:z.boolean().default(true)},
    annotations:{readOnlyHint:false,openWorldHint:false,destructiveHint:false}
  },async({objective,priority,dryRun})=>{
    const id=randomUUID(), route=plan(objective,priority);
    const mission={id,objective,priority,dryRun,status:dryRun?"simulated":"queued",route,createdAt:new Date().toISOString()};
    missions.set(id,mission);
    return jsonResult({mission},dryRun?`Mission ${id} simulated safely.`:`Mission ${id} queued in the NEXUS-100 control plane.`);
  });

  server.registerTool("get_mission",{
    title:"Get mission status",
    description:"Read the current state and route of a NEXUS-100 mission by ID.",
    inputSchema:{missionId:z.string().uuid()},
    annotations:{readOnlyHint:true,openWorldHint:false,destructiveHint:false}
  },async({missionId})=>{
    const mission=missions.get(missionId);
    if(!mission) return {isError:true,content:[{type:"text",text:"Mission not found."}]};
    return jsonResult({mission},`Mission ${missionId} is ${mission.status}.`);
  });

  server.registerTool("request_sensitive_action",{
    title:"Request approval for a sensitive action",
    description:"Create an approval-gated proposal for a consequential action such as deployment, deletion, spending, repository modification, or external communication. This tool never executes the action.",
    inputSchema:{missionId:z.string().uuid().optional(),action:z.string().min(3).max(1000),reason:z.string().min(3).max(2000),risk:z.enum(["medium","high","critical"]).default("high")},
    annotations:{readOnlyHint:false,openWorldHint:false,destructiveHint:false}
  },async({missionId,action,reason,risk})=>{
    const approval={id:randomUUID(),missionId:missionId||null,action,reason,risk,status:"awaiting_human_approval",createdAt:new Date().toISOString()};
    return jsonResult({approval},`Approval ${approval.id} created. No external action was executed.`);
  });

  return server;
}

const httpServer=createServer(async(req,res)=>{
  const url=new URL(req.url||"/",`http://${req.headers.host||"localhost"}`);
  if(req.method==="GET"&&url.pathname==="/health"){res.writeHead(200,{"content-type":"application/json"}).end(JSON.stringify({status:"ok",service:"nexus-100-mcp",version:"1.0.0"}));return;}
  if(req.method==="OPTIONS"&&url.pathname===MCP_PATH){res.writeHead(204,{"Access-Control-Allow-Origin":"*","Access-Control-Allow-Methods":"POST, GET, DELETE, OPTIONS","Access-Control-Allow-Headers":"content-type, mcp-session-id, authorization","Access-Control-Expose-Headers":"Mcp-Session-Id"});res.end();return;}
  if(url.pathname===MCP_PATH&&["POST","GET","DELETE"].includes(req.method||"")){
    if(!authOk(req)){res.writeHead(401,{"content-type":"application/json","www-authenticate":"Bearer"}).end(JSON.stringify({error:"unauthorized"}));return;}
    const len=Number(req.headers["content-length"]||0); if(len>MAX_BODY){res.writeHead(413).end("Payload Too Large");return;}
    res.setHeader("Access-Control-Allow-Origin","*");res.setHeader("Access-Control-Expose-Headers","Mcp-Session-Id");
    const server=makeServer();const transport=new StreamableHTTPServerTransport({sessionIdGenerator:undefined,enableJsonResponse:true});
    res.on("close",()=>{transport.close();server.close();});
    try{await server.connect(transport);await transport.handleRequest(req,res);}
    catch(err){console.error("MCP request failed",err);if(!res.headersSent)res.writeHead(500,{"content-type":"application/json"}).end(JSON.stringify({error:"internal_error"}));}
    return;
  }
  res.writeHead(404,{"content-type":"application/json"}).end(JSON.stringify({error:"not_found"}));
});
httpServer.requestTimeout=30_000;httpServer.headersTimeout=10_000;httpServer.keepAliveTimeout=5_000;
httpServer.listen(PORT,"0.0.0.0",()=>console.log(`NEXUS-100 MCP listening on :${PORT}${MCP_PATH}`));

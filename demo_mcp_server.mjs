import { createInterface } from "readline";
const rl = createInterface({ input: process.stdin });
const send = (o) => process.stdout.write(JSON.stringify(o) + "\n")
rl.on("line", (line) => {
    const m = JSON.parse(line);
    if (m.method === "initialize") send({ 
        jsonrpc: "2.0", 
        id: m.id, 
        result: { 
            protocolVersion: "2024-11-05", 
            capabilities: { 
                tools: {} }, 
                serverInfo: { 
                    name: "demo", 
                    version: "1" 
                } 
            } 
        });
    else if (m.method === "tools/list") send({ 
        jsonrpc: "2.0", 
        id: m.id, 
        result: { 
            tools: [{
                name: "add", 
                description: "Add two numbers", 
                inputSchema: { 
                    type: "object", 
                    properties: { 
                        a: { type: "number"}, 
                        b: { type: "number"} }, 
                        required: ["a", "b"] 
                    } 
                }] 
            } 
        })
    else if (m.method === "tools/call") send({
        jsonrpc: "2.0",
        id: m.id,
        result: {
            content: [{
                type: "text",
                text: String(m.params.arguments.a + m.params.arguments.b) 
            }]
        }
    });
});